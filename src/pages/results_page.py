"""Results page showing AI recommendations after student evaluation."""
import streamlit as st

from src.styles import scroll_to_top


def render_results_page():
    """Display recommendations page."""
    scroll_to_top()

    student_id = (
        st.session_state.form_data.get("s_id", "")
        if "form_data" in st.session_state
        else ""
    )

    st.title(f"Рекомендації для дитини ({student_id})")

    st.markdown("""
    Дякуємо за завершення оцінювання!

    У повній версії системи тут з'являться персоналізовані рекомендації
    на основі штучного інтелекту.
    """)

    st.divider()

    if st.button("Оцінити систему"):
        st.session_state.show_feedback = True
        st.rerun()
