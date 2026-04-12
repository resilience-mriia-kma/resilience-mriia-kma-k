"""Database connection and persistence functions for the resilience assessment app."""
import os

import psycopg2
from pgvector.psycopg2 import register_vector


def connect_to_db():
    """
    Підключення до бази даних pgvector на сервері
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        # реєструємо тип даних 'vector' для нашого RAG
        register_vector(conn)
        return conn
    except Exception as e:  # pylint: disable=broad-except
        print(f"Помилка підключення: {e}")
        return None


def save_feedback(feedback) -> bool:
    """Save a FeedbackSubmission to the feedbacks table, creating it if needed."""
    conn = connect_to_db()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedbacks (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT NOW(),
                teacher_id VARCHAR(20),
                experience VARCHAR(50),
                grades TEXT,
                subject TEXT,
                completed VARCHAR(20),
                students_count VARCHAR(20),
                ease_of_use INTEGER,
                acceptability_1 INTEGER, acceptability_2 INTEGER,
                acceptability_3 INTEGER,
                appropriateness_1 INTEGER, appropriateness_2 INTEGER,
                appropriateness_3 INTEGER,
                feasibility_1 INTEGER, feasibility_2 INTEGER,
                feasibility_3 INTEGER,
                usability_1 INTEGER, usability_2 INTEGER,
                usability_3 INTEGER,
                llm_1 INTEGER, llm_2 INTEGER,
                llm_3 INTEGER, llm_4 INTEGER,
                safety_1 INTEGER, safety_2 INTEGER, safety_3 INTEGER,
                intention_1 INTEGER, intention_2 INTEGER,
                open_1 TEXT, open_2 TEXT, open_3 TEXT, open_4 TEXT,
                helped_understand VARCHAR(20),
                changes_made TEXT
            )
        """)
        grades_str = ", ".join(feedback.grades) if feedback.grades else None
        cur.execute("""
            INSERT INTO feedbacks (
                teacher_id, experience, grades, subject,
                completed, students_count, ease_of_use,
                acceptability_1, acceptability_2, acceptability_3,
                appropriateness_1, appropriateness_2, appropriateness_3,
                feasibility_1, feasibility_2, feasibility_3,
                usability_1, usability_2, usability_3,
                llm_1, llm_2, llm_3, llm_4,
                safety_1, safety_2, safety_3,
                intention_1, intention_2,
                open_1, open_2, open_3, open_4,
                helped_understand, changes_made
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            feedback.teacher_id, feedback.experience,
            grades_str, feedback.subject,
            feedback.completed, feedback.students_count,
            feedback.ease_of_use,
            feedback.acceptability_1, feedback.acceptability_2,
            feedback.acceptability_3,
            feedback.appropriateness_1, feedback.appropriateness_2,
            feedback.appropriateness_3,
            feedback.feasibility_1, feedback.feasibility_2,
            feedback.feasibility_3,
            feedback.usability_1, feedback.usability_2,
            feedback.usability_3,
            feedback.llm_1, feedback.llm_2,
            feedback.llm_3, feedback.llm_4,
            feedback.safety_1, feedback.safety_2,
            feedback.safety_3,
            feedback.intention_1, feedback.intention_2,
            feedback.open_1, feedback.open_2,
            feedback.open_3, feedback.open_4,
            feedback.helped_understand, feedback.changes_made,
        ))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:  # pylint: disable=broad-except
        print(f"Помилка збереження відгуку: {e}")
        conn.rollback()
        conn.close()
        return False