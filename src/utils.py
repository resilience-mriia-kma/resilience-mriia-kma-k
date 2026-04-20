"""Utility functions for session state management, ID generation, and AI submission."""
import hashlib
import os
import uuid

import streamlit as st
from src.constants import QUESTIONS


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
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        return api_key
    
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:  # pylint: disable=broad-except
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
        st.toast("API ключ ще не налаштовано.")
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

    # Analytics and access control
    if "submission_id" not in st.session_state:
        st.session_state.submission_id = None
    if "can_rate_system" not in st.session_state:
        st.session_state.can_rate_system = False


def reset_evaluation_state():
    """Reset evaluation state for a new student assessment."""
    st.session_state.evaluation_complete = False
    st.session_state.current_step = 0
    st.session_state.completed_steps = set()
    st.session_state.student_data_locked = False
    st.session_state.start_time = None
    st.session_state.submission_id = str(uuid.uuid4())
    
    # Initialize form data with empty structure (never set to None)
    st.session_state.form_data = {
        "t_id": st.session_state.teacher_id,
        "s_id": "",
        "age": 10,
        "gender": "Чоловіча",
        "answers": {factor: [None] * len(questions) for factor, questions in QUESTIONS.items()},
        "question_comments": {factor: [""] * len(questions) for factor, questions in QUESTIONS.items()}
    }


def lock_student_data():
    """Lock student identification data after first step."""
    st.session_state.student_data_locked = True


def build_ai_submission(form_data: dict):
    """
    Build TeacherFormSubmission object from form data.
    
    Args:
        form_data: Dictionary containing all form responses
        
    Returns:
        TeacherFormSubmission: Pydantic model ready for AI agent
    """
    from schemas import TeacherFormSubmission  # pylint: disable=import-outside-toplevel
    
    factor_names = list(QUESTIONS.keys())
    calculated_scores = calculate_factor_scores(form_data, factor_names)
    
    # Map factor names to schema fields
    factor_mapping = {
        "Підтримка сім'ї": ("family_support", "family_support_comments"),
        "Оптимізм": ("optimism", "optimism_comments"),
        "Цілеспрямованість та копінг": ("coping", "coping_comments"),
        "Соціальні зв'язки": ("social_connections", "social_connections_comments"),
        "Здоров'я": ("health", "health_comments")
    }
    
    # Build submission data
    submission_data = {
        "teacher_id": form_data["t_id"],
        "student_id": form_data["s_id"],
        "student_age": form_data["age"],
        "student_gender": form_data["gender"]
    }
    
    # Add scores and comments for each factor
    for factor_name, (score_key, comments_key) in factor_mapping.items():
        submission_data[f"{score_key}_score"] = calculated_scores.get(factor_name, 0)
        submission_data[comments_key] = form_data["question_comments"].get(factor_name, [])
    
    return TeacherFormSubmission(**submission_data)


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
            calculated_scores[factor] = 0  # Default value if all NA
    
    return calculated_scores

def build_semantic_student_profile(form_data: dict) -> str:
    """Translates raw 0-2 scores into a detailed text narrative for the LLM."""

    strengths = []  # Scores of 2
    weaknesses = []  # Scores of 0

    for factor, questions_list in QUESTIONS.items():
        answers = form_data.get("answers", {}).get(factor, [])

        for i, ans in enumerate(answers):
            if not ans or ans.startswith("NA"):
                continue

            score = int(ans[0])
            question_text = questions_list[i]

            if score == 2:
                strengths.append(f"- {question_text}")
            elif score == 0:
                weaknesses.append(f"- {question_text}")

    profile = "Детальний профіль учня:\n\n"

    if weaknesses:
        profile += "🔴 ЗОНИ УВАГИ (Потребують термінової підтримки):\n"
        profile += "\n".join(weaknesses) + "\n\n"
    else:
        profile += "🔴 ЗОНИ УВАГИ: Явних критичних проблем не виявлено.\n\n"

    if strengths:
        profile += "🟢 СИЛЬНІ СТОРОНИ (Ресурс для спирання):\n"
        profile += "\n".join(strengths) + "\n\n"

    return profile
