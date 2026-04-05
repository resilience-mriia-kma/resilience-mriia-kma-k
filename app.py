import streamlit as st
from rag_agent import ResilienceAgent

from src.constants import QUESTIONS, OPTIONS, PRIVACY_POLICY
from src.utils import (
    generate_teacher_id,
    validate_api_key_available,
    initialize_session_state,
    reset_evaluation_state,
    lock_student_data,
    build_ai_submission
)
from src.styles import apply_custom_styles, render_stepper, scroll_to_top

# Page configuration
st.set_page_config(
    page_title="Помічник педагога",
    page_icon="👤",
    layout="centered"
)


apply_custom_styles()
initialize_session_state()


def render_consent_page():
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
        help="Ваш адреса ніде НЕ зберігатиметься. Використовується лише для створення унікального анонімного ID."
    )
    
    consent_checkbox = st.checkbox(
        "Я прочитав(-ла) інформацію про обробку даних і надаю згоду на участь у дослідженні.",
        key="consent_checkbox"
    )
    
    if st.button("Перейти до опитування", type="primary", use_container_width=True):
        if not teacher_email or teacher_email.strip() == "":
            st.toast("Введіть електронну адресу.")
        elif not (teacher_email.strip().endswith("@ukma.edu.ua") or teacher_email.strip().endswith("@gmail.com")):
            st.error("Дозволено лише @ukma.edu.ua або @gmail.com")
        elif not consent_checkbox:
            st.toast("Для продовження необхідно дати згоду на участь у дослідженні.")
        else:
            # Generate teacher ID
            generated_id = generate_teacher_id(teacher_email.strip())
            st.session_state.teacher_id = generated_id
            st.session_state.consent_given = True
            
            st.toast(f"Згенеровано анонімний ID: {generated_id}")
            st.rerun()


def render_results_page():
    """Display AI recommendations after evaluation."""
    scroll_to_top()
    
    st.title("Опитування")
    st.markdown("### Результати аналізу")
    
    if "ai_recommendations" in st.session_state and st.session_state.ai_recommendations:
        st.markdown(st.session_state.ai_recommendations)
    else:
        st.info("Рекомендації генеруються...")
    
    st.caption("⚠️ Штучний інтелект може помилятися. Будь ласка, перевіряйте важливу інформацію.")


def render_step_0():
    """Render student identification step."""
    st.subheader("Загальна інформація")
    st.caption("Крок 1 з 6")
    
    col1, col2 = st.columns(2)
    with col1:
        t_id = st.text_input(
            "ID педагога",
            value=st.session_state.teacher_id,
            disabled=True,
            help="Ваш ID вже згенеровано автоматично",
            key="t_id_display"
        )
        s_id = st.text_input(
            "ID учня",
            value=st.session_state.form_data["s_id"],
            placeholder="STU-001",
            help="Використовуйте умовний код БЕЗ імен чи прізвищ",
            key="s_id_input",
            disabled=st.session_state.student_data_locked
        )
        st.session_state.form_data["s_id"] = s_id
        st.session_state.form_data["t_id"] = t_id
    
    with col2:
        age = st.number_input(
            "Вік учня (від 6 до 18 років)",
            min_value=6,
            max_value=18,
            value=st.session_state.form_data["age"],
            key="age_input",
            disabled=st.session_state.student_data_locked
        )
        st.session_state.form_data["age"] = age
        
        gender = st.selectbox(
            "Стать учня",
            ["Чоловіча", "Жіноча"],
            index=0 if st.session_state.form_data["gender"] == "Чоловіча" else 1,
            key="gender_input",
            disabled=st.session_state.student_data_locked
        )
        st.session_state.form_data["gender"] = gender
    
    if st.session_state.student_data_locked:
        st.caption("Зміна даних учня заблокована на цьому етапі.")
    
    st.divider()
    
    if st.button("Далі", key="next_btn_step0", type="primary", use_container_width=True):
        if not st.session_state.form_data["s_id"]:
            st.toast("Вкажіть ID учня.")
        else:
            lock_student_data()
            st.session_state.completed_steps.add(0)
            st.session_state.current_step = 1
            st.rerun()


def render_factor_step(step_number, factor_name, questions):
    """Render a factor evaluation step with questions and comments."""
    st.subheader(factor_name)
    st.caption(f"Крок {step_number + 1} з 6")
    
    for q_idx, q in enumerate(questions):
        current_answer = st.session_state.form_data["answers"][factor_name][q_idx]
        ans = st.radio(
            f"**{q}**",
            OPTIONS,
            key=f"q_{step_number}_{q_idx}",
            index=OPTIONS.index(current_answer) if current_answer in OPTIONS else None,
            horizontal=True
        )
        st.session_state.form_data["answers"][factor_name][q_idx] = ans
        
        current_comment = st.session_state.form_data["question_comments"][factor_name][q_idx]
        comment = st.text_input(
            "Коментар (необов'язково)",
            value=current_comment,
            key=f"comment_{step_number}_{q_idx}",
            placeholder="Опишіть власні спостереження..."
        )
        st.session_state.form_data["question_comments"][factor_name][q_idx] = comment
        st.divider()
    
    st.divider()
    
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("Назад", key="back_btn", use_container_width=True):
            st.session_state.current_step -= 1
            st.rerun()
    
    with nav_col2:
        all_answered = all(ans is not None for ans in st.session_state.form_data["answers"][factor_name])
        
        if step_number < 5:
            if st.button("Далі", key="next_btn", type="primary", use_container_width=True):
                if not all_answered:
                    st.toast("Надайте відповіді на всі запитання, щоб продовжити.")
                else:
                    st.session_state.completed_steps.add(step_number)
                    st.session_state.current_step += 1
                    st.rerun()
        else:
            if st.button("Отримати рекомендації", key="submit_btn", type="primary", use_container_width=True):
                if not all_answered:
                    st.toast("Надайте відповіді на всі запитання.")
                else:
                    submit_evaluation()


def submit_evaluation():
    """Handle final submission and AI generation."""
    factor_names = list(QUESTIONS.keys())
    
    # Validate all steps
    validation_errors = []
    for factor in factor_names:
        if None in st.session_state.form_data["answers"][factor]:
            validation_errors.append(f"Пропущені запитання у блоці: {factor}")
    
    if validation_errors:
        st.toast("Будь ласка, заповніть всі обов'язкові поля: " + ", ".join(validation_errors))
        return
    
    if not validate_api_key_available():
        st.stop()
    
    # Build submission using helper
    submission = build_ai_submission(st.session_state.form_data)
    
    with st.spinner("ШІ аналізує профіль та шукає доказові практики..."):
        try:
            agent = ResilienceAgent()
            result = agent.generate_advice(submission)
            
            st.session_state.ai_recommendations = result
            st.session_state.students_evaluated += 1
            st.session_state.evaluation_complete = True
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"Сталася помилка при зверненні до ШІ: {e}")


def render_questionnaire():
    """Main questionnaire flow with stepper."""
    scroll_to_top()
    
    st.title("Опитування")
    
    with st.expander("Інструкція з оцінювання та трактовка балів", expanded=False):
        st.markdown(f"""
        ### Як користуватися системою
        1. **Ідентифікація**: Вкажіть анонімний код учня, його вік та стать. Ці дані будуть заблоковані після переходу до оцінювання для забезпечення цілісності даних.
        2. **Покрокове оцінювання**: Пройдіть послідовно через 5 факторів резильєнтності. За необхідності є можливість повернутися назад.
        3. **Текстові спостереження**: В кінці кожного блоку ви можете додати опис конкретних ситуацій. Це **необов'язково**, але допоможе ШІ надати значно точніші та індивідуальні поради.
        4. **Фінал**: Після завершення всіх кроків натисніть "Отримати рекомендації".

        ### Що означають оцінки
        Будь ласка, оцінюйте поведінку учня, базуючись на спостереженнях за останні **2-4 тижні**:
        * **0 — Низький рівень**: Поведінка проявляється рідко або не спостерігається. Дитина потребує значної підтримки дорослого.
        * **1 — Середній рівень**: Поведінка проявляється час від часу, в окремих ситуаціях або лише за підказки/підтримки дорослого.
        * **2 — Високий рівень**: Поведінка проявляється регулярно і стабільно. Дитина демонструє її самостійно у відповідних ситуаціях.
        * **NA — Недостатньо інформації**: У вас не було можливості спостерігати за цією поведінкою у даного учня.

        **Важливо:** Всі запитання є обов'язковими для надання відповіді.
        """)
    
    st.markdown("")
    st.markdown("### Прогрес оцінювання")
    
    stepper_labels = ["Загальна інформація", "Фактор 1", "Фактор 2", "Фактор 3", "Фактор 4", "Фактор 5"]
    stepper_html = render_stepper(stepper_labels, st.session_state.current_step, st.session_state.completed_steps)
    st.markdown(stepper_html, unsafe_allow_html=True)
    st.divider()
    
    # Initialize form data
    if "form_data" not in st.session_state or st.session_state.form_data is None:
        st.session_state.form_data = {
            "t_id": st.session_state.teacher_id,
            "s_id": "",
            "age": 10,
            "gender": "Чоловіча",
            "answers": {factor: [None] * len(questions) for factor, questions in QUESTIONS.items()},
            "question_comments": {factor: [""] * len(questions) for factor, questions in QUESTIONS.items()}
        }
    
    if st.session_state.current_step == 0:
        render_step_0()
    elif 1 <= st.session_state.current_step <= 5:
        factor_names = list(QUESTIONS.keys())
        current_factor = factor_names[st.session_state.current_step - 1]
        current_questions = QUESTIONS[current_factor]
        render_factor_step(st.session_state.current_step, current_factor, current_questions)


if not st.session_state.consent_given:
    render_consent_page()
elif st.session_state.evaluation_complete:
    render_results_page()
else:
    render_questionnaire()

