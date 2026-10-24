"""Google Gemini integration with automatic model fallback.

Flow per request:
  1. Try each model in the chain (GEMINI_MODELS env, else built-in defaults).
  2. Transient errors (5xx, network, timeout) -> retry same model with backoff, then move on.
  3. Quota (429), model not found (404), bad request, empty/blocked output -> move on immediately.
  4. Bad/invalid API key -> stop at once (every model would fail the same way).
  5. If the whole chain fails, auto-discover other Gemini flash models available to the key and try those.
The API key is always passed in, never hardcoded.
"""
import logging
import os
import random
import threading
import time

from google import genai
from google.genai import types

log = logging.getLogger(__name__)

DEFAULT_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
]
MAX_RETRIES = 2            # extra attempts per model for transient errors
BACKOFF_BASE = 1.0         # seconds: 1s, 2s (+ jitter)
TIMEOUT_MS = 30_000
MAX_CHARS = 12000
_EXCLUDE = ("image", "tts", "audio", "live", "embed", "native", "robotics", "computer", "vision", "omni")

SYSTEM = (
    "You are an expert technical recruiter and ATS resume coach. Be concise, specific and honest. "
    "Never invent experience, employers, metrics or skills the candidate did not provide; "
    "if a number is needed, use a placeholder like [X%] for the candidate to fill in."
)

_state = threading.local()


class GeminiError(RuntimeError):
    """Raised when no model could produce an answer."""


class GeminiAuthError(GeminiError):
    """Invalid / missing / revoked API key."""


class _Skip(Exception):
    """Internal: give up on this model, try the next one."""


def get_last_model() -> str:
    """Model that produced the most recent successful response in this thread."""
    return getattr(_state, "model", "")


def model_chain(preferred: str = None) -> list:
    env_list = [m.strip() for m in os.getenv("GEMINI_MODELS", "").split(",") if m.strip()]
    single = os.getenv("GEMINI_MODEL", "").strip()
    chain = ([preferred] if preferred else []) + env_list + ([single] if single else []) + DEFAULT_MODELS
    seen, out = set(), []
    for m in chain:
        m = m.replace("models/", "")
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _classify(exc: Exception) -> str:
    """Return 'auth' | 'retry' | 'skip'."""
    code = getattr(exc, "code", None)
    msg = str(exc).lower()
    if code == 401 or ("api key" in msg and any(w in msg for w in ("invalid", "not valid", "expired", "leaked", "revoked"))):
        return "auth"
    if code in (500, 502, 503, 504) or code is None:   # server errors, timeouts, network issues
        return "retry"
    return "skip"                                       # 400, 403, 404, 429, ...


def _short(exc: Exception) -> str:
    return " ".join(str(exc).split())[:160]


def _call_model(client, model: str, prompt: str, cfg) -> str:
    last = ""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
            text = (getattr(resp, "text", None) or "").strip()
            if not text:
                raise _Skip("empty or blocked response")
            return text
        except _Skip:
            raise
        except Exception as e:  # noqa: BLE001
            kind = _classify(e)
            last = _short(e)
            if kind == "auth":
                raise GeminiAuthError("Gemini API key was rejected. Check the key in the sidebar or .env.") from e
            if kind == "skip":
                raise _Skip(last) from e
            if attempt < MAX_RETRIES:
                delay = BACKOFF_BASE * (2 ** attempt) + random.uniform(0, 0.4)
                log.warning("%s transient error (%s); retry in %.1fs", model, last, delay)
                time.sleep(delay)
    raise _Skip(f"failed after {MAX_RETRIES + 1} attempts: {last}")


def _discover(client, exclude: set) -> list:
    """Ask the API which flash models this key can use (newest names first)."""
    found = []
    try:
        for m in client.models.list():
            name = (getattr(m, "name", "") or "").replace("models/", "")
            actions = getattr(m, "supported_actions", None) or []
            if ("generateContent" in actions and "flash" in name
                    and not any(x in name for x in _EXCLUDE) and name not in exclude):
                found.append(name)
    except Exception as e:  # noqa: BLE001
        log.warning("model discovery failed: %s", _short(e))
    return sorted(found, reverse=True)[:4]


def _generate(api_key: str, prompt: str, model: str = None) -> str:
    if not api_key:
        raise GeminiAuthError("No Gemini API key configured.")
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=TIMEOUT_MS))
    cfg = types.GenerateContentConfig(system_instruction=SYSTEM)

    failures, tried = [], set()

    def run(models):
        for m in models:
            tried.add(m)
            try:
                text = _call_model(client, m, prompt, cfg)
                _state.model = m
                if failures:
                    log.info("Fell back to %s after: %s", m, "; ".join(failures))
                return text
            except _Skip as s:
                failures.append(f"{m}: {s}")
        return None

    text = run(model_chain(model))
    if text is None:
        text = run(_discover(client, tried))
    if text is None:
        raise GeminiError("All Gemini models failed.\n" + "\n".join(f"- {f}" for f in failures))
    return text


# ----------------------------------------------------------------- features --
def review_resume(api_key: str, resume_text: str, jd_text: str = "",
                  missing_keywords=None, model: str = None) -> str:
    jd_block = f"\n\nJOB DESCRIPTION:\n{jd_text[:MAX_CHARS]}" if jd_text.strip() else ""
    kw_block = f"\n\nKeywords missing per ATS scan: {', '.join(missing_keywords)}" if missing_keywords else ""
    prompt = f"""Review this resume for ATS and recruiter impact.

RESUME:
{resume_text[:MAX_CHARS]}{jd_block}{kw_block}

Respond in markdown with exactly these sections:
### Top 5 improvements
(numbered, specific, actionable)
### Rewritten bullets
(pick the 4 weakest bullets and rewrite each as: Before -> After. Use strong action verbs.)
### Tailored summary
(2-3 lines{', tailored to the job description' if jd_text.strip() else ''})
### Keyword guidance
(where truthfully to work in missing keywords; say which ones to skip if the candidate has no evidence)"""
    return _generate(api_key, prompt, model)
