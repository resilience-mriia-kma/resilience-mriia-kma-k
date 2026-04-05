"""
Utility functions for the Resilience Assessment System
Includes ID generation and API key management.
"""

import hashlib
import os
import streamlit as st


def generate_teacher_id(email: str) -> str:
    """
    Generate a 6-character unique ID from email using SHA256.
    
    Args:
        email: Teacher's email address
        
    Returns:
        str: Unique teacher ID in format TCH-XXXXXX
    """
    hash_object = hashlib.sha256(email.encode())
    hex_dig = hash_object.hexdigest()
    return f"TCH-{hex_dig[:6].upper()}"


def get_openai_api_key() -> str | None:
    """
    Get OpenAI API key with fallback logic.
    Checks environment variable first, then Streamlit secrets.
    
    Returns:
        str | None: API key if found, None otherwise
    """
    # Try environment variable first
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        return api_key
    
    # Try Streamlit secrets
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    
    return None


def validate_api_key_available() -> bool:
    """
    Check if API key is available and show warning if not.
    
    Returns:
        bool: True if API key is available, False otherwise
    """
    api_key = get_openai_api_key()
    
    if not api_key:
        st.toast(
            "API ключ не налаштовано. Будь ласка, налаштуйте OPENAI_API_KEY у секретах або .env файлі.",
            icon="⚠️"
        )
        return False
    
    return True


def initialize_session_state():
    """Initialize all required session state variables."""
    
    # Consent and navigation
    if "consent_given" not in st.session_state:
        st.session_state.consent_given = False
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Оцінка учня"
    
    # Evaluation tracking
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    
    if "students_evaluated" not in st.session_state:
        st.session_state.students_evaluated = 0
    
    if "teacher_id" not in st.session_state:
        st.session_state.teacher_id = ""
    
    if "evaluation_complete" not in st.session_state:
        st.session_state.evaluation_complete = False
    
    # Step navigation
    if "current_step" not in st.session_state:
        st.session_state.current_step = 0
    
    if "completed_steps" not in st.session_state:
        st.session_state.completed_steps = set()
    
    # Student data lock
    if "student_data_locked" not in st.session_state:
        st.session_state.student_data_locked = False


def reset_evaluation_state():
    """Reset evaluation state for a new student assessment."""
    st.session_state.evaluation_complete = False
    st.session_state.current_step = 0
    st.session_state.completed_steps = set()
    st.session_state.student_data_locked = False
    st.session_state.start_time = None
    
    # Clear form data
    if "form_data" in st.session_state:
        st.session_state.form_data = None


def lock_student_data():
    """Lock student identification data after first step."""
    st.session_state.student_data_locked = True


def calculate_factor_scores(form_data: dict, factor_names: list) -> dict:
    """
    Calculate average scores for each resilience factor.
    
    Args:
        form_data: Dictionary containing all form responses
        factor_names: List of factor names
        
    Returns:
        dict: Dictionary mapping factor names to calculated scores
    """
    calculated_scores = {}
    
    for factor in factor_names:
        answers = form_data["answers"][factor]
        numeric_answers = [
            int(a[0]) for a in answers 
            if a and not a.startswith("NA")
        ]
        
        if numeric_answers:
            calculated_scores[factor] = round(sum(numeric_answers) / len(numeric_answers))
        else:
            calculated_scores[factor] = 1  # Default value if all NA
    
    return calculated_scores
