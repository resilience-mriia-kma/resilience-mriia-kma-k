"""Main entry point for the Помічник педагога Streamlit application."""

import streamlit as st
from dotenv import load_dotenv

from src.database import init_db
from src.pages.consent_page import render_consent_page
from src.pages.feedback_page import render_feedback_form
from src.pages.questionnaire_page import render_questionnaire
from src.pages.results_page import render_results_page
from src.styles import apply_custom_styles
from src.utils import initialize_session_state

load_dotenv()

st.set_page_config(page_title="Помічник педагога", page_icon="👤", layout="centered")


@st.cache_resource
def _initialize_database():
    """Run schema initialization once per app instance.

    @st.cache_resource ensures init_db() runs only on the first script
    execution rather than on every Streamlit rerun.
    """
    init_db()
    return True


_initialize_database()
apply_custom_styles()
initialize_session_state()

if not st.session_state.consent_given:
    render_consent_page()
elif st.session_state.get("show_feedback", False):
    render_feedback_form()
elif st.session_state.evaluation_complete:
    render_results_page()
else:
    render_questionnaire()
