import os
from openai import OpenAI
from src.database import connect_to_db
from src.utils import build_semantic_student_profile  # Import your new function


class ResilienceAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.db = connect_to_db()

    def _get_system_prompt(self) -> str:
        return """
        Ти — експертний помічник педагога. Твоя мета: надати 3-5 практичних рекомендацій для вчителя щодо учня.
        Відповідай українською мовою.

        ПРАВИЛА БЕЗПЕКИ:
        1. НІКОЛИ не став медичних або психологічних діагнозів.
        2. НІКОЛИ не використовуй слова "депресія", "травма", "розлад".
        3. Ти інструмент підтримки вчителя, а не психотерапевт.
        """

    def _retrieve_knowledge(self, semantic_profile: str, limit: int = 3) -> str:
        """Семантичний пошук релевантних фрагментів у knowledge_base.

        Повертає пустий рядок, якщо база порожня або сталася помилка —
        це дозволяє generate_advice() повністю пропустити блок промпту.

        Логи (видимі в `docker compose logs resilience-app`) показують:
        - чи метод викликався
        - скільки чанків повернулося
        - distance найближчих джерел (менше = ближче)
        - повний текст кожного отриманого чанку
        """
        if not semantic_profile:
            print("[RAG] _retrieve_knowledge: empty profile, skipping")
            return ""
        try:
            response = self.client.embeddings.create(
                input=semantic_profile,
                model="text-embedding-3-small",
            )
            query_vector = response.data[0].embedding

            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT content, source_file, embedding <-> %s::vector AS distance
                FROM knowledge_base
                ORDER BY embedding <-> %s::vector
                LIMIT %s
                """,
                (query_vector, query_vector, limit),
            )
            results = cursor.fetchall()
            cursor.close()

            if not results:
                print("[RAG] _retrieve_knowledge: 0 chunks returned (knowledge_base is empty?)")
                return ""

            print(
                f"[RAG] _retrieve_knowledge: {len(results)} chunks, "
                f"top distance={results[0][2]:.4f}"
            )
            for i, (content, source, distance) in enumerate(results, start=1):
                print(f"[RAG] ─── #{i}  source={source}  distance={distance:.4f} ───")
                # Prefix each line of content with [RAG] so `grep RAG` still
                # surfaces the chunk text alongside the metadata lines.
                for line in content.splitlines():
                    print(f"[RAG] {line}")
                print(f"[RAG] ─── end #{i} ───")

            chunks = [f"[Джерело: {source}]\n{content}" for content, source, _ in results]
            return "\n\n---\n\n".join(chunks)

        except Exception as e:  # pylint: disable=broad-except
            print(f"[RAG] Помилка пошуку в базі знань: {e}")
            return ""

    def _retrieve_contrastive_examples(self, profile_text: str) -> dict:
        """Витягує і найкращі, і найгірші приклади для подібних профілів"""
        try:
            response = self.client.embeddings.create(
                input=profile_text,
                model="text-embedding-3-small"
            )
            query_vector = response.data[0].embedding
            cursor = self.db.cursor()

            cursor.execute("""
                SELECT llm_response FROM ai_learning_memory 
                WHERE avg_score >= 4.0 ORDER BY embedding <-> %s::vector LIMIT 1
            """, (query_vector,))
            positive = cursor.fetchone()

            cursor.execute("""
                SELECT llm_response, teacher_critique FROM ai_learning_memory 
                WHERE avg_score <= 2.5 ORDER BY embedding <-> %s::vector LIMIT 1
            """, (query_vector,))
            negative = cursor.fetchone()

            return {
                "good": positive[0] if positive else None,
                "bad_response": negative[0] if negative else None,
                "bad_critique": negative[1] if negative else None
            }
        except Exception as e:
            print(f"Помилка пошуку contrastive_examples: {e}")
            return {"good": None, "bad_response": None, "bad_critique": None}

    def generate_advice(self, form_data: dict, comments_summary: list) -> str:

        semantic_profile = build_semantic_student_profile(form_data)

        retrieved_knowledge = self._retrieve_knowledge(semantic_profile)
        examples = self._retrieve_contrastive_examples(semantic_profile)

        # Knowledge base block — only included if we actually retrieved something.
        knowledge_prompt = ""
        if retrieved_knowledge:
            knowledge_prompt = f"""
            НАУКОВІ ДАНІ З БАЗИ ЗНАНЬ:
            {retrieved_knowledge}
            """

        contrastive_prompt = ""
        if examples["good"]:
            contrastive_prompt += f"\nПРИКЛАД ВДАЛОЇ ВІДПОВІДІ (наслідуй цей стиль та формат):\n{examples['good']}\n"

        if examples["bad_response"]:
            contrastive_prompt += f"""
            ПРИКЛАД НЕВДАЛОЇ ВІДПОВІДІ:
            {examples["bad_response"]}

            КОМЕНТАР ВЧИТЕЛЯ ЩОДО ЦІЄЇ ПОМИЛКИ: 
            "{examples["bad_critique"]}"

            ЗАВДАННЯ: Враховуй цей коментар вчителя. Не роби помилок, описаних у невдалому прикладі.
            """

        user_prompt = f"""
        Ось спостереження за учнем:

        {semantic_profile}

        Коментарі вчителя:
        {chr(10).join(comments_summary) if comments_summary else 'не вказано'}

        {knowledge_prompt}

        {contrastive_prompt}

        Згенеруй практичні рекомендації. Спирайся на "Сильні сторони" учня, щоб вирішити проблеми у "Зонах уваги".
        """

        # Final summary line — confirms KB was included and shows total prompt size.
        print(
            f"[RAG] generate_advice: prompt={len(user_prompt)} chars, "
            f"kb_included={bool(retrieved_knowledge)}, "
            f"good_example={bool(examples['good'])}, "
            f"bad_example={bool(examples['bad_response'])}"
        )

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
