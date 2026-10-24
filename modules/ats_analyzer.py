"""ATS scoring engine: keyword match, sections, contact info, action verbs, metrics, length."""
import re
from collections import Counter
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .constants import (ACTION_VERBS, REQUIRED_SECTIONS, SECTION_PATTERNS,
                        SKILL_DB, STOPWORDS)

EMAIL_RE = r"[\w.+-]+@[\w-]+\.[\w.-]+"
PHONE_RE = r"(\+?\d[\d\s().-]{8,}\d)"
LINKEDIN_RE = r"linkedin\.com/in/"
GITHUB_RE = r"github\.com/"
METRIC_RE = r"\b\d+(\.\d+)?\s?(%|x|k|m|\+)|\b\d{2,}\b|\$\s?\d+|₹\s?\d+"


@dataclass
class AnalysisResult:
    total: int = 0
    breakdown: dict = field(default_factory=dict)       # name -> (score, max)
    matched: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    sections_found: list = field(default_factory=list)
    sections_missing: list = field(default_factory=list)
    similarity: float = 0.0
    word_count: int = 0
    suggestions: list = field(default_factory=list)


def _has(term: str, text: str) -> bool:
    return re.search(rf"(?<![\w+#]){re.escape(term)}(?![\w+#])", text) is not None


def extract_keywords(jd: str, top_n: int = 15) -> list:
    """Skills found in the JD first, then the most frequent remaining terms."""
    jd_l = jd.lower()
    skills = [s for s in SKILL_DB if _has(s, jd_l)]
    tokens = [t for t in re.findall(r"[a-z][a-z+#./-]{1,}", jd_l)
              if t not in STOPWORDS and len(t) > 2]
    bigrams = [f"{a} {b}" for a, b in zip(tokens, tokens[1:])]
    bigram_counts = Counter(bigrams)
    counts = Counter(tokens) + Counter({b: c for b, c in bigram_counts.items() if c > 1})
    extra = []
    for term, _ in counts.most_common(60):
        if term in skills or any(term in s or s in term for s in skills):
            continue
        extra.append(term)
        if len(extra) >= top_n:
            break
    return skills + extra


def _similarity(resume: str, jd: str) -> float:
    try:
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform([resume, jd])
        return float(cosine_similarity(vec[0], vec[1])[0][0])
    except ValueError:
        return 0.0


def analyze(resume_text: str, jd_text: str = "") -> AnalysisResult:
    text = resume_text.lower()
    res = AnalysisResult()
    res.word_count = len(text.split())
    has_jd = bool(jd_text.strip())

    # --- 1. Keyword match (40) -------------------------------------------------
    if has_jd:
        keywords = extract_keywords(jd_text)
        res.matched = [k for k in keywords if _has(k, text)]
        res.missing = [k for k in keywords if k not in res.matched]
        ratio = len(res.matched) / len(keywords) if keywords else 0
        res.similarity = _similarity(resume_text, jd_text)
        kw_score = round(30 * ratio + 10 * min(res.similarity * 2, 1))
    else:
        res.matched = [s for s in SKILL_DB if _has(s, text)]
        kw_score = round(40 * min(len(res.matched) / 15, 1))
    res.breakdown["Keyword match" if has_jd else "Skill coverage"] = (kw_score, 40)

    # --- 2. Sections (20) -----------------------------------------------------
    for name, pat in SECTION_PATTERNS.items():
        if re.search(pat, text):
            res.sections_found.append(name)
    res.sections_missing = [s for s in REQUIRED_SECTIONS if s not in res.sections_found]
    sec_score = round(20 * (len(REQUIRED_SECTIONS) - len(res.sections_missing)) / len(REQUIRED_SECTIONS))
    res.breakdown["Sections"] = (sec_score, 20)

    # --- 3. Contact info (10) -------------------------------------------------
    contact = {
        "email": bool(re.search(EMAIL_RE, resume_text)),
        "phone": bool(re.search(PHONE_RE, resume_text)),
        "LinkedIn": bool(re.search(LINKEDIN_RE, text)),
        "GitHub": bool(re.search(GITHUB_RE, text)),
    }
    contact_score = (4 if contact["email"] else 0) + (3 if contact["phone"] else 0) \
        + (2 if contact["LinkedIn"] else 0) + (1 if contact["GitHub"] else 0)
    res.breakdown["Contact info"] = (contact_score, 10)

    # --- 4. Action verbs (10) -------------------------------------------------
    words = set(re.findall(r"[a-z]+", text))
    verbs_used = ACTION_VERBS & words
    res.breakdown["Action verbs"] = (round(10 * min(len(verbs_used) / 8, 1)), 10)

    # --- 5. Quantified impact (10) -------------------------------------------
    metrics = [m for m in re.finditer(METRIC_RE, resume_text, flags=re.I)]
    res.breakdown["Quantified impact"] = (round(10 * min(len(metrics) / 5, 1)), 10)

    # --- 6. Length (10) ------------------------------------------------------
    wc = res.word_count
    len_score = 10 if 300 <= wc <= 800 else 6 if 200 <= wc < 300 or 800 < wc <= 1000 else 2
    res.breakdown["Length"] = (len_score, 10)

    res.total = min(sum(s for s, _ in res.breakdown.values()), 100)

    # --- Suggestions ---------------------------------------------------------
    if res.sections_missing:
        res.suggestions.append(f"Add missing section(s): {', '.join(res.sections_missing)}.")
    if not contact["email"]:
        res.suggestions.append("Add a professional email address.")
    if not contact["phone"]:
        res.suggestions.append("Add a phone number.")
    if not contact["LinkedIn"]:
        res.suggestions.append("Add your LinkedIn URL.")
    if not contact["GitHub"]:
        res.suggestions.append("Add your GitHub profile (important for developer / SDET roles).")
    if len(verbs_used) < 8:
        res.suggestions.append("Start bullets with strong action verbs (built, automated, optimized, deployed...).")
    if len(metrics) < 5:
        res.suggestions.append("Quantify impact with numbers (e.g., 'reduced load time by 30%', '500+ users').")
    if wc < 300:
        res.suggestions.append("Resume looks thin; expand projects and experience with concrete detail.")
    elif wc > 800:
        res.suggestions.append("Resume is long; trim to 1 page (fresher) or 2 pages (experienced).")
    if has_jd and res.missing:
        res.suggestions.append("Naturally include missing keywords where truthful: "
                               + ", ".join(res.missing[:8]) + ".")
    if not res.suggestions:
        res.suggestions.append("Strong resume. Tailor keywords per job description for best results.")
    return res
