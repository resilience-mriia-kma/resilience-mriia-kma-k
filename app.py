import streamlit as st
from schemas import TeacherFormSubmission
from rag_agent import ResilienceAgent

# Налаштування сторінки
st.set_page_config(page_title="Помічник Педагога", page_icon="", layout="centered")

st.title("Помічник Педагога")
st.markdown("**Система оцінки резильєнтності та генерації науково обґрунтованих рекомендацій.**")
st.divider()

# Створюємо форму
with st.form("resilience_form"):
    st.subheader("1. Ідентифікація")
    col1, col2 = st.columns(2)
    with col1:
        t_id = st.text_input("Ваш ID (вчителя)", placeholder="напр., TCH-001")
        s_id = st.text_input("Анонімний ID учня", placeholder="напр., STU-104")
    with col2:
        age = st.number_input("Вік учня", min_value=6, max_value=18, value=10)
        gender = st.selectbox("Стать", ["Чоловіча", "Жіноча", "Інше"])

    st.subheader("2. Оцінка факторів резильєнтності")
    st.caption("0 - Низький рівень, 1 - Середній рівень, 2 - Високий рівень")
    
    f_family = st.slider("Підтримка сім'ї", 0, 2, 1)
    f_opt = st.slider("Оптимізм", 0, 2, 1)
    f_coping = st.slider("Цілеспрямованість / копінг", 0, 2, 1)
    f_social = st.slider("Соціальні зв'язки", 0, 2, 1)
    f_health = st.slider("Здоров'я", 0, 2, 1)

    comment = st.text_area("Додаткові спостереження (необов'язково)")

    # Кнопка відправки
    submitted = st.form_submit_button("Аналізувати та отримати рекомендації", type="primary")

    if submitted:
        if not t_id or not s_id:
            st.error("Будь ласка, заповніть ID вчителя та учня.")
        else:
            # Валідація даних через Pydantic (schemas.py)
            submission = TeacherFormSubmission(
                teacher_id=t_id, student_id=s_id, student_age=age, student_gender=gender,
                family_support_score=f_family, optimism_score=f_opt, coping_score=f_coping,
                social_connections_score=f_social, health_score=f_health, teacher_comment=comment
            )

            with st.spinner("ШІ аналізує профіль та шукає доказові практики у базі знань..."):
                try:
                    # Викликаємо агента
                    agent = ResilienceAgent()
                    result = agent.generate_advice(submission)
                    
                    st.success("Аналіз завершено!")
                    st.markdown("### 📋 Ваші рекомендації:")
                    st.info(result)
                except Exception as e:
                    st.error(f"Сталася помилка при зверненні до LLM або Бази Даних: {e}")