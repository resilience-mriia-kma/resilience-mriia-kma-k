import os
from openai import OpenAI
from database import connect_to_db
from schemas import TeacherFormSubmission

class ResilienceAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.db = connect_to_db()

def _get_system_prompt(self) -> str:
    return """
    You are an expert AI assistant for school teachers.
    Your goal: provide 3-5 practical recommendations for a teacher about a student.
    Always respond in Ukrainian.

    SAFETY RULES:
    1. NEVER make medical or psychological diagnoses.
    2. NEVER use words like "depression", "trauma", "disorder".
    3. You are a teacher support tool, not a psychotherapist.

    TEXT ADAPTATION RULES:
    Translate abstract scientific terms into simple classroom actions:
    - "emotional regulation training" -> "ask the child to take 3 deep breaths"
    - "family intervention" -> "send parents a short positive message about the student"
    """

    def _retrieve_knowledge(self, scores: dict) -> str:
        """Витягує релевантні поради з векторної бази pgvector"""
        # Формуємо текстовий запит на основі низьких балів
        low_factors = [factor for factor, score in scores.items() if score == 0]
        query = f"поради для підтримки учня з низькими балами: {', '.join(low_factors)}"
        
        # Отримуємо embedding для запиту
        response = self.client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_vector = response.data[0].embedding
        
        # Шукаємо схожі записи в pgvector
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT content FROM knowledge_base
            ORDER BY embedding <-> %s::vector
            LIMIT 5
        """, (query_vector,))
        
        results = cursor.fetchall()
        return "\n".join([row[0] for row in results])

    def generate_advice(self, submission: TeacherFormSubmission) -> str:
        scores = {
            "Підтримка сім'ї": submission.family_support_score,
            "Оптимізм": submission.optimism_score,
            "Цілеспрямованість": submission.coping_score,
            "Соціальні зв'язки": submission.social_connections_score,
            "Здоров'я": submission.health_score,
        }
        
        retrieved_knowledge = self._retrieve_knowledge(scores)
        
        user_prompt = f"""
        Оцінки учня (0=низький, 1=середній, 2=високий):
        {scores}

        Коментар вчителя: {submission.teacher_comment or 'не вказано'}

        НАУКОВІ ДАНІ З БАЗИ ЗНАНЬ (ВИКОРИСТОВУЙ ТІЛЬКИ ЦЕ):
        {retrieved_knowledge}

        Напиши коротку інструкцію для вчителя маркованими списками.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.choices[0].message.content