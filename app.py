"""
Помічник Педагога - Resilience Assessment System
Main application entry point with modular architecture.
"""

import streamlit as st
import time
from schemas import TeacherFormSubmission
from rag_agent import ResilienceAgent

# Import modular components
from src.constants import QUESTIONS, OPTIONS, PRIVACY_POLICY, SCORE_DEFINITIONS, FACTOR_ICONS
from src.utils import (
    generate_teacher_id,
    validate_api_key_available,
    initialize_session_state,
    reset_evaluation_state,
    lock_student_data,
    calculate_factor_scores
)
from src.styles import apply_custom_styles

# Page configuration
st.set_page_config(
    page_title="Помічник педагога",
    page_icon="👤",
    layout="centered"
)

# Apply custom styles
apply_custom_styles()

# Initialize session state
initialize_session_state()


# ========== GATEKEEPER: CONSENT SCREEN ==========
if not st.session_state.consent_given:
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
            st.toast("Будь ласка, введіть вашу електронну адресу!", icon="⚠️")
        elif not (teacher_email.strip().endswith("@ukma.edu.ua") or teacher_email.strip().endswith("@gmail.com")):
            st.error("Дозволено лише @ukma.edu.ua або @gmail.com")
        elif not consent_checkbox:
            st.toast("Для продовження необхідно дати згоду на участь у дослідженні!", icon="⚠️")
        else:
            # Generate teacher ID
            generated_id = generate_teacher_id(teacher_email.strip())
            st.session_state.teacher_id = generated_id
            st.session_state.consent_given = True
            
            # Show success toast
            st.toast(f"Згенеровано анонімний ID: {generated_id}")
            time.sleep(2)
            st.rerun()

# ========== MAIN APP (AFTER CONSENT) ==========
else:
    # Check if user should see feedback form
    if "show_feedback" not in st.session_state:
        st.session_state.show_feedback = False
    
    # ========== FEEDBACK FORM (after 10 students) ==========
    if st.session_state.show_feedback:
        st.title("Оцінка системи")
        
        st.markdown("""
        ### Дякуємо за використання системи!
        
        Ви оцінили 10 учнів. Будь ласка, поділіться вашими враженнями про роботу системи.
        Ваш відгук допоможе нам покращити інструмент для педагогів.
        """)
        
        with st.form("feedback_form"):
            st.subheader("Ваш відгук")
            
            usefulness = st.slider(
                "Наскільки корисною виявилася система?",
                min_value=1,
                max_value=5,
                value=3,
                help="1 = Зовсім не корисна, 5 = Дуже корисна"
            )
            
            ease_of_use = st.slider(
                "Наскільки зручною була система у використанні?",
                min_value=1,
                max_value=5,
                value=3,
                help="1 = Дуже незручна, 5 = Дуже зручна"
            )
            
            ai_quality = st.slider(
                "Наскільки якісними були рекомендації ШІ?",
                min_value=1,
                max_value=5,
                value=3,
                help="1 = Низька якість, 5 = Висока якість"
            )
            
            feedback_text = st.text_area(
                "Додаткові коментарі та пропозиції:",
                placeholder="Поділіться вашими думками про систему...",
                height=150
            )
            
            submitted = st.form_submit_button("Надіслати відгук", type="primary", use_container_width=True)
            
            if submitted:
                st.success("Дякуємо за ваш відгук! Він допоможе нам покращити систему.")
                st.balloons()
                st.divider()
                
        # Return to evaluation button (outside form to avoid nesting issues)
        if submitted:
            if st.button("📊 Повернутися до оцінювання наступного учня", type="primary", use_container_width=True):
                reset_evaluation_state()
                st.session_state.show_feedback = False
                st.session_state.evaluation_complete = False
                st.rerun()
    
    # ========== MAIN EVALUATION FLOW ==========
    else:
        st.title("Опитування")
        
        # Collapsible instructions
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
        
        # Results screen with actual AI recommendations
        if st.session_state.evaluation_complete:
            st.markdown("### Результати аналізу")
            
            # Display AI recommendations if available
            if "ai_recommendations" in st.session_state and st.session_state.ai_recommendations:
                st.markdown(st.session_state.ai_recommendations)
            else:
                st.info("Рекомендації генеруються...")
            
            st.caption("⚠️ Штучний інтелект може помилятися. Будь ласка, перевіряйте важливу інформацію.")
            
            st.divider()
            
            # Navigation buttons (no Back button - results are final)
            col1, col2 = st.columns(2)
            
            with col1:
                # Option to evaluate another student
                if st.button("➕ Оцінити наступного учня", use_container_width=True):
                    reset_evaluation_state()
                    st.rerun()
            
            with col2:
                # Feedback form button (no 10 student requirement)
                if st.button("📝 Оцінити систему", type="primary", use_container_width=True):
                    st.session_state.show_feedback = True
                    st.rerun()
            
            st.stop()
        
        # Invisible anchor for scroll-to-top
        st.markdown('<div id="top"></div>', unsafe_allow_html=True)
        
        # Scroll to top on step change
        st.markdown(
            '<script>window.parent.document.querySelector("section.main").scrollTo(0,0);</script>',
            unsafe_allow_html=True
        )
        
        # Start timer
        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()
        
        # Define all steps (0 = Загальна інформація, 1-5 = factors)
        factor_names = list(QUESTIONS.keys())
        # Stepper labels: simplified format
        stepper_labels = ["Загальна інформація", "Фактор 1", "Фактор 2", "Фактор 3", "Фактор 4", "Фактор 5"]
        
        # Visual Stepper with uniform width
        st.markdown("")
        st.markdown("### Прогрес оцінювання")
        
        # Create stepper HTML with flexbox for uniform width
        stepper_html = "<div style='display: flex; gap: 0.5rem; margin-bottom: 1rem;'>"
        for idx, step_label in enumerate(stepper_labels):
            if idx in st.session_state.completed_steps:
                stepper_html += f"<div class='step-completed'>{step_label}</div>"
            elif idx == st.session_state.current_step:
                stepper_html += f"<div class='step-current'><strong>{step_label}</strong></div>"
            else:
                stepper_html += f"<div class='step-locked'>{step_label}</div>"
        stepper_html += "</div>"
        
        st.markdown(stepper_html, unsafe_allow_html=True)
        
        st.divider()
        
        # Store form data in session state to persist across reruns
        # Initialize if None or doesn't exist
        if "form_data" not in st.session_state or st.session_state.form_data is None:
            st.session_state.form_data = {
                "t_id": st.session_state.teacher_id,
                "s_id": "",
                "age": 10,
                "gender": "Чоловіча",
                "answers": {factor: [None] * len(questions) for factor, questions in QUESTIONS.items()},
                "question_comments": {factor: [""] * len(questions) for factor, questions in QUESTIONS.items()}
            }
        
        # Step 0: Загальна інформація (Identification)
        if st.session_state.current_step == 0:
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
                
                # Student ID - locked after first step
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
                # Age - locked after first step
                age = st.number_input(
                    "Вік учня (від 6 до 18 років)", 
                    min_value=6, 
                    max_value=18, 
                    value=st.session_state.form_data["age"],
                    key="age_input",
                    disabled=st.session_state.student_data_locked
                )
                st.session_state.form_data["age"] = age
                
                # Gender - locked after first step
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
            
            # Navigation for Step 0 - Full width button
            if st.button("Далі", key="next_btn_step0", type="primary", use_container_width=True):
                if not st.session_state.form_data["s_id"]:
                    st.toast("Вкажіть ID учня.")
                else:
                    # Lock student data after leaving Step 0
                    lock_student_data()
                    st.session_state.completed_steps.add(0)
                    st.session_state.current_step = 1
                    st.rerun()
        
        # Steps 1-5: Factor evaluation
        elif 1 <= st.session_state.current_step <= 5:
            current_factor = factor_names[st.session_state.current_step - 1]
            current_questions = QUESTIONS[current_factor]
            
            st.subheader(current_factor)
            st.caption(f"Крок {st.session_state.current_step + 1} з 6")
            
            # Display questions for current factor with individual comments
            for q_idx, q in enumerate(current_questions):
                current_answer = st.session_state.form_data["answers"][current_factor][q_idx]
                ans = st.radio(
                    f"**{q}**", 
                    OPTIONS, 
                    key=f"q_{st.session_state.current_step}_{q_idx}",
                    index=OPTIONS.index(current_answer) if current_answer in OPTIONS else None,
                    horizontal=True
                )
                st.session_state.form_data["answers"][current_factor][q_idx] = ans
                
                # Individual comment input for each question
                current_comment = st.session_state.form_data["question_comments"][current_factor][q_idx]
                comment = st.text_input(
                    "Коментар (необов'язково)",
                    value=current_comment,
                    key=f"comment_{st.session_state.current_step}_{q_idx}",
                    placeholder="Опишіть конкретну ситуацію..."
                )
                st.session_state.form_data["question_comments"][current_factor][q_idx] = comment
                
                st.divider()
            
            st.divider()
            
            # Navigation buttons
            nav_col1, nav_col2 = st.columns(2)
            
            with nav_col1:
                if st.button("Назад", key="back_btn", use_container_width=True):
                    st.session_state.current_step -= 1
                    st.rerun()
            
            with nav_col2:
                # Validation for current step - only check if all questions answered
                all_answered = all(ans is not None for ans in st.session_state.form_data["answers"][current_factor])
                
                if st.session_state.current_step < 5:
                    if st.button("Далі", key="next_btn", type="primary", use_container_width=True):
                        if not all_answered:
                            st.toast("Надайте відповіді на всі запитання, щоб продовжити.")
                        else:
                            st.session_state.completed_steps.add(st.session_state.current_step)
                            st.session_state.current_step += 1
                            st.rerun()
                else:
                    # Last step - show final submit button
                    if st.button("Отримати рекомендації", key="submit_btn", type="primary", use_container_width=True):
                        if not all_answered:
                            st.toast("Будь ласка, дайте відповідь на всі запитання", icon="⚠️")
                        else:
                            # Validate all previous steps
                            validation_errors = []
                            
                            for factor in factor_names:
                                if None in st.session_state.form_data["answers"][factor]:
                                    validation_errors.append(f"Пропущені запитання у блоці: {factor}")
                            
                            if validation_errors:
                                error_msg = "Будь ласка, заповніть всі обов'язкові поля: " + ", ".join(validation_errors)
                                st.toast(error_msg, icon="⚠️")
                            else:
                                # Check API key before proceeding
                                if not validate_api_key_available():
                                    st.stop()
                                
                                # Calculate scores
                                calculated_scores = calculate_factor_scores(st.session_state.form_data, factor_names)
                                time_taken = int(time.time() - st.session_state.start_time)
                                
                                # Map factor names to schema fields
                                factor_mapping = {
                                    "Підтримка сім'ї": ("family_support", "family_support_comments"),
                                    "Оптимізм": ("optimism", "optimism_comments"),
                                    "Цілеспрямованість та копінг": ("coping", "coping_comments"),
                                    "Соціальні зв'язки": ("social_connections", "social_connections_comments"),
                                    "Здоров'я": ("health", "health_comments")
                                }
                                
                                # Build submission with individual comments
                                submission_data = {
                                    "teacher_id": st.session_state.form_data["t_id"],
                                    "student_id": st.session_state.form_data["s_id"],
                                    "student_age": st.session_state.form_data["age"],
                                    "student_gender": st.session_state.form_data["gender"],
                                    "time_taken_seconds": time_taken
                                }
                                
                                # Add scores and comments for each factor
                                for factor_name, (score_key, comments_key) in factor_mapping.items():
                                    submission_data[f"{score_key}_score"] = calculated_scores.get(factor_name, 1)
                                    submission_data[comments_key] = st.session_state.form_data["question_comments"].get(factor_name, [])
                                
                                submission = TeacherFormSubmission(**submission_data)
                                
                                # Call AI agent
                                with st.spinner("ШІ аналізує профіль та шукає доказові практики..."):
                                    try:
                                        agent = ResilienceAgent()
                                        result = agent.generate_advice(submission)
                                        
                                        # Store AI result in session state
                                        st.session_state.ai_recommendations = result
                                        st.session_state.students_evaluated += 1
                                        st.session_state.evaluation_complete = True
                                        
                                        # Show celebration
                                        st.balloons()
                                        st.rerun()
                                        
                                    except Exception as e:
                                        st.error(f"Сталася помилка при зверненні до ШІ: {e}")
