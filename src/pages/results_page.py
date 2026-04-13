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

    st.title(f"{student_id}: рекомендації")

    st.markdown("""
    Дякуємо за завершення оцінювання!

    У повній версії системи тут з'являться персоналізовані рекомендації
    на основі штучного інтелекту.
    """)

    st.divider()

    if st.session_state.get("can_rate_system", False):
        if st.button("Оцінити систему", type="primary"):
            st.session_state.show_feedback = True
            st.rerun()
