"""Feedback form page for teacher evaluation of the AI assistant system."""
import streamlit as st
from pydantic import ValidationError

from schemas import FeedbackSubmission
from src.database import save_feedback
from src.styles import scroll_to_top
from src.utils import reset_evaluation_state


def render_feedback_form():
    """Render the comprehensive 11-block teacher feedback form."""
    scroll_to_top()
    
    st.title("Форма зворотнього зв'язку")
    st.markdown("### Оцінка використання ШІ-агента \"Помічник педагога\"")
    
    with st.form("feedback_form"):
        st.subheader("1. Загальна інформація")
        
        col1, col2 = st.columns(2)
        with col1:
            experience = st.radio(
                "Ваш стаж педагогічної діяльності:",
                ["До 3 років", "3–10 років", "10–20 років", "Більше 20 років"],
                key="experience"
            )
        
        with col2:
            grades = st.multiselect(
                "Класи, з якими Ви працюєте:",
                ["Початкова школа", "Середня школа", "Старша школа"],
                key="grades"
            )
        
        subject = st.text_input("Предмет:", placeholder="Вкажіть предмети, які Ви викладаєте...", key="subject")
        
        st.divider()
        
        st.subheader("2. Досвід використання інструменту")
        
        col1, col2 = st.columns(2)
        with col1:
            completed = st.radio(
                "Чи змогли Ви завершити оцінювання учнів за допомогою інструменту?",
                ["Так", "Частково", "Ні"],
                key="completed"
            )
            
            students_count = st.radio(
                "Скільки учнів Ви оцінили?",
                ["1–3", "4–7", "8–12", "Більше 12"],
                key="students_count"
            )
        
        with col2:
            ease_of_use = st.select_slider(
                "Наскільки легко було використовувати інструмент?\n(1 — дуже складно, 5 — дуже легко)",
                options=[1, 2, 3, 4, 5],
                value=3,
                key="ease_of_use"
            )
        
        st.divider()
        
        st.subheader("3. Прийнятність")
        st.caption("Наскільки Ви погоджуєтесь з твердженнями:")
        
        acceptability_1 = st.select_slider(
            "Інструмент є корисним у моїй роботі",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="acceptability_1"
        )
        
        acceptability_2 = st.select_slider(
            "Мені було комфортно використовувати цей інструмент",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="acceptability_2"
        )
        
        acceptability_3 = st.select_slider(
            "Я б рекомендував(-ла) цей інструмент іншим вчителям",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="acceptability_3"
        )
        
        st.divider()
        
        st.subheader("4. Відповідність")
        
        appropriateness_1 = st.select_slider(
            "Інструмент відповідає потребам моїх учнів",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="appropriateness_1"
        )
        
        appropriateness_2 = st.select_slider(
            "Інструмент відповідає умовам моєї школи",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="appropriateness_2"
        )
        
        appropriateness_3 = st.select_slider(
            "Питання інструменту відображають реальні ситуації в класі",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="appropriateness_3"
        )
        
        st.divider()
        
        st.subheader("5. Здійсненність")
        
        feasibility_1 = st.select_slider(
            "Я можу використовувати цей інструмент у своїй щоденній роботі",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="feasibility_1"
        )
        
        feasibility_2 = st.select_slider(
            "Заповнення інструменту не займає надто багато часу",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="feasibility_2"
        )
        
        feasibility_3 = st.select_slider(
            "Я розумію, як інтегрувати цей інструмент у свою практику",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="feasibility_3"
        )
        
        st.divider()
        
        st.subheader("6. Зручність використання")
        
        usability_1 = st.select_slider(
            "Інтерфейс системи є зрозумілим",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="usability_1"
        )
        
        usability_2 = st.select_slider(
            "Інструкції були зрозумілими",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="usability_2"
        )
        
        usability_3 = st.select_slider(
            "Я легко орієнтувався(лась) у системі",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="usability_3"
        )
        
        st.divider()
        
        st.subheader("7. Оцінка ШІ-агента")
        
        llm_1 = st.select_slider(
            "Рекомендації системи були зрозумілими",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="llm_1"
        )
        
        llm_2 = st.select_slider(
            "Рекомендації виглядали релевантними до ситуацій учнів",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="llm_2"
        )
        
        llm_3 = st.select_slider(
            "Рекомендації були практичними для використання",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="llm_3"
        )
        
        llm_4 = st.select_slider(
            "Я довіряю рекомендаціям системи",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="llm_4"
        )
        
        st.divider()
        
        st.subheader("8. Безпека та етика")
        
        safety_1 = st.select_slider(
            "Система не створює ризику стигматизації учнів",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="safety_1"
        )
        
        safety_2 = st.select_slider(
            "Я розумію обмеження системи",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="safety_2"
        )
        
        safety_3 = st.select_slider(
            "Я не сприймаю рекомендації як \"діагноз\"",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="safety_3"
        )
        
        st.divider()
        
        st.subheader("9. Намір використання")
        
        intention_1 = st.select_slider(
            "Я б використовував(-ла) цей інструмент у майбутньому",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="intention_1"
        )
        
        intention_2 = st.select_slider(
            "Я б використовував(-ла) цей інструмент регулярно",
            options=[1, 2, 3, 4, 5],
            value=3,
            key="intention_2"
        )
        
        st.divider()
        
        st.subheader("10. Відкриті питання")
        
        open_1 = st.text_area(
            "Що було найбільш корисним у цьому інструменті?",
            placeholder="Ваша відповідь...",
            key="open_1",
            height=100
        )
        
        open_2 = st.text_area(
            "Що було незрозумілим або складним?",
            placeholder="Ваша відповідь...",
            key="open_2",
            height=100
        )
        
        open_3 = st.text_area(
            "Чи були рекомендації, які викликали сумніви або дискомфорт?",
            placeholder="Ваша відповідь...",
            key="open_3",
            height=100
        )
        
        open_4 = st.text_area(
            "Які зміни Ви б запропонували?",
            placeholder="Ваша відповідь...",
            key="open_4",
            height=100
        )
        
        st.divider()
        
        st.subheader("11. Досвід роботи з учнями")
        
        col1, col2 = st.columns(2)
        with col1:
            helped_understand = st.radio(
                "Чи допоміг інструмент Вам краще зрозуміти учнів?",
                ["Так", "Частково", "Ні"],
                key="helped_understand"
            )
        
        with col2:
            changes_made = st.text_area(
                "Чи змінили Ви щось у своїй роботі після використання інструменту?",
                placeholder="Ваша відповідь...",
                key="changes_made",
                height=100
            )
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            back_btn = st.form_submit_button(
                "Повернутись до оцінки учнів",
                type="primary",
                use_container_width=True
            )
        with col2:
            submit_btn = st.form_submit_button(
                "Надіслати відгук",
                type="primary",
                use_container_width=True
            )
        
        if submit_btn:
            form_data = {
                "teacher_id": st.session_state.get("teacher_id"),
                "submission_id": st.session_state.get("submission_id"),
                "experience": experience,
                "grades": grades,
                "subject": subject or None,
                "completed": completed,
                "students_count": students_count,
                "ease_of_use": ease_of_use,
                "acceptability_1": acceptability_1,
                "acceptability_2": acceptability_2,
                "acceptability_3": acceptability_3,
                "appropriateness_1": appropriateness_1,
                "appropriateness_2": appropriateness_2,
                "appropriateness_3": appropriateness_3,
                "feasibility_1": feasibility_1,
                "feasibility_2": feasibility_2,
                "feasibility_3": feasibility_3,
                "usability_1": usability_1,
                "usability_2": usability_2,
                "usability_3": usability_3,
                "llm_1": llm_1,
                "llm_2": llm_2,
                "llm_3": llm_3,
                "llm_4": llm_4,
                "safety_1": safety_1,
                "safety_2": safety_2,
                "safety_3": safety_3,
                "intention_1": intention_1,
                "intention_2": intention_2,
                "open_1": open_1 or None,
                "open_2": open_2 or None,
                "open_3": open_3 or None,
                "open_4": open_4 or None,
                "helped_understand": helped_understand,
                "changes_made": changes_made or None,
            }
            try:
                submission = FeedbackSubmission(**form_data)
                saved = save_feedback(submission)
                if saved:
                    st.success(
                        "Дякуємо за ваш відгук! "
                        "Цей внесок суттєво допоможе вдосконалити систему."
                    )
                else:
                    st.warning(
                        "Відгук не вдалося зберегти. "
                        "Перевірте з'єднання з базою даних."
                    )
                st.session_state.feedback_submitted = True
            except ValidationError as exc:
                st.error(f"Помилка валідації: {exc}")
        
        if back_btn:
            st.session_state.show_feedback = False
            st.session_state.feedback_submitted = False
            reset_evaluation_state()
            st.rerun()
