"""Consent and registration page for the teacher onboarding flow."""
import streamlit as st

from src.constants import PRIVACY_POLICY
from src.utils import generate_teacher_id


def render_consent_page():
    """Render the informed consent and email registration page."""
    st.title("Помічник педагога")

    st.markdown("""
    ### Вітаємо у системі оцінки резильєнтності учнів!

    Дякуємо за ваш інтерес до участі у нашому дослідженні. Ця система допоможе вам:
    - Оцінити рівень резильєнтності ваших учнів за 5 науково обґрунтованими факторами
    - Отримати персоналізовані рекомендації на основі штучного інтелекту
    - Доступ до доказових практик підтримки резильєнтності

    **Перед початком роботи, будь ласка, уважно прочитайте інформацію нижче.**
    """)

    st.divider()

    with st.expander("Політика збору та обробки даних", expanded=False):
        st.markdown(PRIVACY_POLICY)

    st.divider()

    st.subheader("Інформована згода")

    teacher_email = st.text_input(
        "Введіть Вашу електронну адресу:",
        placeholder="yourname@ukma.edu.ua",
        help=(
            "Ваш адреса ніде НЕ зберігатиметься. "
            "Використовується лише для створення унікального анонімного ID."
        )
    )

    consent_checkbox = st.checkbox(
        "Я прочитав(-ла) інформацію про обробку даних і надаю згоду на участь у дослідженні.",
        key="consent_checkbox"
    )

    if st.button("Перейти до опитування", type="primary", use_container_width=True):
        if not teacher_email or teacher_email.strip() == "":
            st.toast("Введіть електронну адресу.")
        elif not (
            teacher_email.strip().endswith("@ukma.edu.ua")
            or teacher_email.strip().endswith("@gmail.com")
        ):
            st.error("Дозволено лише @ukma.edu.ua або @gmail.com")
        elif not consent_checkbox:
            st.toast("Для продовження необхідно дати згоду на участь у дослідженні.")
        else:
            generated_id = generate_teacher_id(teacher_email.strip())
            st.session_state.teacher_id = generated_id
            st.session_state.consent_given = True

            st.toast(f"Згенеровано ID: {generated_id}")
            st.rerun()
