"""Index documents from a directory into the knowledge_base table.

Usage (inside the resilience-app container):
    docker compose exec resilience-app python /app/scripts/index_kb.py
    docker compose exec resilience-app python /app/scripts/index_kb.py --reset
    docker compose exec resilience-app python /app/scripts/index_kb.py --path /app/kb

Supports .txt, .md, and .docx files. Each file is split into chunks
(paragraph-aware, capped at ~1000 chars), embedded with
text-embedding-3-small, and inserted into the knowledge_base table.
"""

import argparse
import os
import sys
from pathlib import Path

from openai import OpenAI

# Make `src` importable when this script is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import connect_to_db, init_db  # noqa: E402

EMBEDDING_MODEL = "text-embedding-3-small"
MAX_CHUNK_CHARS = 1000
SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx"}


def read_txt(path: Path) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_docx(path: Path) -> str:
    # Imported lazily so users without docx files don't need python-docx
    # available on the import path during a dry run.
    from docx import Document

    doc = Document(str(path))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def read_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".txt", ".md"}:
        return read_txt(path)
    if ext == ".docx":
        return read_docx(path)
    raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Paragraph-aware chunker. Greedily packs paragraphs into ~max_chars chunks.

    Falls back to hard char-count splitting only for paragraphs that exceed
    max_chars on their own (rare for prose).
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        # Oversized paragraph: emit what we have, then split the paragraph itself.
        if len(para) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(para), max_chars):
                chunks.append(para[i : i + max_chars])
            continue

        prospective = (current + "\n\n" + para) if current else para
        if len(prospective) <= max_chars:
            current = prospective
        else:
            chunks.append(current)
            current = para

    if current:
        chunks.append(current)
    return chunks


def embed(client: OpenAI, text: str) -> list[float]:
    response = client.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return response.data[0].embedding


def index_directory(kb_path: Path, reset: bool = False) -> None:
    if not kb_path.exists():
        print(f"Шлях не існує: {kb_path}", file=sys.stderr)
        sys.exit(1)

    # Ensure the table exists before we try to write to it.
    init_db()

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    conn = connect_to_db()
    if conn is None:
        print("Не вдалося підключитися до БД", file=sys.stderr)
        sys.exit(1)

    try:
        cur = conn.cursor()

        if reset:
            print("Очищення таблиці knowledge_base...")
            cur.execute("TRUNCATE knowledge_base RESTART IDENTITY")
            conn.commit()

        files = sorted(
            p
            for p in kb_path.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not files:
            print(f"У {kb_path} не знайдено документів ({SUPPORTED_EXTENSIONS}).")
            return

        total_chunks = 0
        for path in files:
            relative = path.relative_to(kb_path)
            print(f"Обробляю: {relative}")
            try:
                text = read_file(path)
            except Exception as e:  # pylint: disable=broad-except
                print(f"  пропущено (помилка читання): {e}")
                continue

            chunks = chunk_text(text)
            if not chunks:
                print("  пропущено (порожній файл)")
                continue

            for idx, chunk in enumerate(chunks):
                vector = embed(client, chunk)
                cur.execute(
                    """
                    INSERT INTO knowledge_base (source_file, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (str(relative), idx, chunk, vector),
                )
            conn.commit()
            print(f"  додано {len(chunks)} чанків")
            total_chunks += len(chunks)

        print(f"\nГотово. Опрацьовано файлів: {len(files)}, чанків: {total_chunks}.")
        cur.close()
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Index documents into knowledge_base")
    parser.add_argument(
        "--path",
        default="/app/kb",
        help="Directory to index (default: /app/kb inside container)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="TRUNCATE knowledge_base before indexing (use for full re-index)",
    )
    args = parser.parse_args()
    index_directory(Path(args.path), reset=args.reset)


if __name__ == "__main__":
    main()
