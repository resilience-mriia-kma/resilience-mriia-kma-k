"""Main entry point for the Помічник педагога Streamlit application."""
from dotenv import load_dotenv
import streamlit as st

from src.utils import initialize_session_state
from src.styles import apply_custom_styles
from src.pages.consent_page import render_consent_page
from src.pages.feedback_page import render_feedback_form
from src.pages.results_page import render_results_page
from src.pages.questionnaire_page import render_questionnaire

load_dotenv()

st.set_page_config(
    page_title="Помічник педагога",
    page_icon="👤",
    layout="centered"
)

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
