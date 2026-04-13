# resilience-mriia-ml
[![Deploy form to server](https://github.com/resilience-mriia-kma/resilience-mriia-kma-k/actions/workflows/actions.yml/badge.svg)](https://github.com/resilience-mriia-kma/resilience-mriia-kma-k/actions/workflows/actions.yml)

## Склад команди: 
- Демʼянік Катерина 
- Саваріна Дарина 
- Титаренко Владислава
- Мигаль Максим

## Структура проєкту

- `src/schemas.py` — Pydantic-моделі для жорсткої валідації вхідних даних від вчителів
- `src/rag_agent.py` — Логіка LLM-агента, системні промпти та інтеграція з базою знань
- `src/database.py` — Підключення до `pgvector` для реалізації семантичного пошуку
