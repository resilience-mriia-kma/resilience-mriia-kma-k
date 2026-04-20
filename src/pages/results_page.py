"""Results page showing AI recommendations after student evaluation."""
import streamlit as st
from src.database import save_llm_generation
from rag_agent import ResilienceAgent

def render_results_page():
     """Display recommendations page."""
    st.title("Рекомендації для вчителя")

    if "current_advice" not in st.session_state:
        agent = ResilienceAgent()

        with st.spinner("Аналізуємо профіль та формуємо рекомендації..."):
            form_data = st.session_state.form_data
            advice_text = agent.generate_advice(form_data, comments_summary=[])

            save_success = save_llm_generation(
                submission_id=st.session_state.submission_id,
                teacher_id=st.session_state.teacher_id,
                form_data=form_data,
                llm_response=advice_text
            )

            if not save_success:
                st.error("Помилка збереження даних, але ви можете переглянути рекомендації.")

            st.session_state.current_advice = advice_text

    st.markdown(st.session_state.current_advice)

    st.divider()

    if st.button("Завершити та оцінити якість", type="primary"):
        st.session_state.show_feedback = True
        st.rerun()

    st.info(f"📋 **Ідентифікатор сесії (Обов'язково зберегти!) :** `{st.session_state.submission_id}`")
