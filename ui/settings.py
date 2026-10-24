"""API key resolution + sidebar widget. Order: sidebar input > st.secrets > environment / .env"""
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _secret() -> str:
    try:
        return st.secrets.get("GEMINI_API_KEY", "") or ""
    except Exception:  # no secrets.toml present
        return ""


def get_api_key() -> str:
    return (st.session_state.get("gemini_key_input", "").strip()
            or _secret()
            or os.getenv("GEMINI_API_KEY", "")
            or os.getenv("GOOGLE_API_KEY", ""))


def sidebar_key_widget():
    st.sidebar.divider()
    st.sidebar.subheader("✨ Gemini AI")
    st.sidebar.text_input("Gemini API key", type="password", key="gemini_key_input",
                          help="Stored only in this browser session. Or set GEMINI_API_KEY in .env / secrets.toml.")
    if get_api_key():
        st.sidebar.success("AI features enabled")
    else:
        st.sidebar.caption("Add a key to enable AI review. Get one at aistudio.google.com/apikey")
