"""Entry point: python -m streamlit run app.py"""
import streamlit as st

from ui import analyzer_page
from ui.settings import sidebar_key_widget

st.set_page_config(page_title="ATS Resume Analyzer", page_icon="📄", layout="wide")

st.sidebar.title("📄 ATS Analyzer")
st.sidebar.caption("Upload a resume, paste a job description, get an ATS score and AI feedback.")
sidebar_key_widget()
analyzer_page.render()
