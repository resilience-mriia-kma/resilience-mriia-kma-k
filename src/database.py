"""Database connection and persistence functions for the resilience assessment app."""

import json
import os
import uuid

import psycopg2
from pgvector.psycopg2 import register_vector


def _raw_connect():
    """Open a psycopg2 connection WITHOUT registering the pgvector type.

    Used by init_db() during bootstrap, when the `vector` extension may not
    yet exist in the target database. All other callers should use
    connect_to_db() instead.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def connect_to_db():
    """
    Підключення до бази даних pgvector на сервері.
    """
    try:
        conn = _raw_connect()
        # реєструємо тип даних 'vector' для нашого RAG
        register_vector(conn)
        return conn
    except Exception as e:  # pylint: disable=broad-except
        print(f"Помилка підключення: {e}")
        return None


def init_db() -> None:
    """Create the pgvector extension and all required tables.

    Idempotent: safe to call on every app startup. Must be called before
    any save_* function so that the schema exists. Order matters —
    `submissions` is created before `ai_learning_memory` because of the
    foreign key dependency.
    """
    conn = _raw_connect()
    try:
        cur = conn.cursor()

        # Enable pgvector — required for the vector(1536) column type
        # and the <-> similarity operator used in rag_agent.py.
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # submissions: one row per LLM generation session.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id VARCHAR(50) PRIMARY KEY,
                teacher_id VARCHAR(20),
                form_data_json TEXT,
                llm_response TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # feedbacks: 11-block teacher feedback form.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedbacks (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT NOW(),
                teacher_id VARCHAR(20),
                submission_id VARCHAR(50),
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

        # ai_learning_memory: RAG store for few-shot retrieval.
        # FK to submissions(id) — that's why submissions is created first.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ai_learning_memory (
                id SERIAL PRIMARY KEY,
                submission_id VARCHAR(50) REFERENCES submissions(id),
                student_profile_text TEXT,
                embedding vector(1536),
                llm_response TEXT,
                avg_score FLOAT,
                teacher_critique TEXT
            )
        """)

        conn.commit()
        cur.close()
    finally:
        conn.close()


def check_has_submissions(teacher_id: str) -> bool:
    """Check whether a teacher has at least one saved student submission."""
    if not teacher_id:
        return False
    conn = connect_to_db()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM submissions WHERE teacher_id = %s LIMIT 1", (teacher_id,)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result is not None
    except Exception as e:  # pylint: disable=broad-except
        print(f"Помилка перевірки submissions: {e}")
        conn.close()
        return False


def save_feedback(feedback) -> bool:
    """Save a FeedbackSubmission to the feedbacks table.

    Assumes init_db() has already been called at app startup.
    """
    conn = connect_to_db()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        grades_str = ", ".join(feedback.grades) if feedback.grades else None
        cur.execute(
            """
            INSERT INTO feedbacks (
                teacher_id, submission_id, experience, grades, subject,
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
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """,
            (
                feedback.teacher_id,
                feedback.submission_id,
                feedback.experience,
                grades_str,
                feedback.subject,
                feedback.completed,
                feedback.students_count,
                feedback.ease_of_use,
                feedback.acceptability_1,
                feedback.acceptability_2,
                feedback.acceptability_3,
                feedback.appropriateness_1,
                feedback.appropriateness_2,
                feedback.appropriateness_3,
                feedback.feasibility_1,
                feedback.feasibility_2,
                feedback.feasibility_3,
                feedback.usability_1,
                feedback.usability_2,
                feedback.usability_3,
                feedback.llm_1,
                feedback.llm_2,
                feedback.llm_3,
                feedback.llm_4,
                feedback.safety_1,
                feedback.safety_2,
                feedback.safety_3,
                feedback.intention_1,
                feedback.intention_2,
                feedback.open_1,
                feedback.open_2,
                feedback.open_3,
                feedback.open_4,
                feedback.helped_understand,
                feedback.changes_made,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:  # pylint: disable=broad-except
        print(f"Помилка збереження відгуку: {e}")
        conn.rollback()
        conn.close()
        return False


def save_llm_generation(
    submission_id: str, teacher_id: str, form_data: dict, llm_response: str
) -> bool:
    """Зберігає сесію генерації. Гарантує наявність ID."""
    if not submission_id:
        submission_id = str(uuid.uuid4())

    conn = connect_to_db()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO submissions (id, teacher_id, form_data_json, llm_response)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """,
            (
                submission_id,
                teacher_id,
                json.dumps(form_data, ensure_ascii=False),
                llm_response,
            ),
        )
        conn.commit()
        return True
    except Exception as e:  # pylint: disable=broad-except
        print(f"Помилка збереження генерації: {e}")
        return False
    finally:
        if conn:
            conn.close()


def save_learning_memory(
    submission_id: str,
    profile_text: str,
    vector: list,
    response_text: str,
    avg_score: float,
    critique: str,
) -> bool:
    """Saves the interaction, score, and critique for future Few-Shot RAG.

    Assumes init_db() has already been called at app startup.
    """
    conn = connect_to_db()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ai_learning_memory (
                submission_id, student_profile_text, embedding,
                llm_response, avg_score, teacher_critique
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (submission_id, profile_text, vector, response_text, avg_score, critique),
        )
        conn.commit()
        return True
    finally:
        if conn:
            conn.close()
