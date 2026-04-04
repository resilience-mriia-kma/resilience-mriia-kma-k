import psycopg2
from pgvector.psycopg2 import register_vector
import os

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
    except Exception as e:
        print(f"Помилка підключення: {e}")
        return None