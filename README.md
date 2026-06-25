---
title: RAG Portfolio Q&A
emoji: 🔎
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# rag-service

> Деплой на Hugging Face Space: задайте секрет `GEMINI_API_KEY` в настройках Space,
> всё остальное (engine=gemini, Qdrant embedded, порт 7860) уже в `Dockerfile`.
> Корпус индексируется автоматически при старте; главная страница `/` — чат для вопросов.

RAG-движок, который отвечает на вопросы о профессиональном опыте по корпусу
документации (проекты, навыки, стек) **с цитированием источников**. Демонстрируется
на собственном портфолио, но индексирует любую папку с `.md` / `.txt` / `.pdf`.

## Архитектура

```
ingest:  data/*.{md,txt,pdf} → chunk → fastembed (локальные эмбеддинги) → Qdrant
query:   вопрос → embed → Qdrant top-k (cosine) → подмешивание контекста в промпт
         → LLM (Codex CLI / claude -p) → ответ + [источники]
```

- **Vector DB:** Qdrant (docker-compose).
- **Эмбеддинги:** `fastembed`, локально, без API-ключей (по умолчанию
  `paraphrase-multilingual-MiniLM-L12-v2` — мультиязычная, понимает русский,
  ~0.2 ГБ; через `EMBED_MODEL` можно поднять до `intfloat/multilingual-e5-large`).
- **Генерация:** Codex CLI (gpt-5.5) основной, `claude -p` фоллбэк — через `rag/llm.py`.
- **Интерфейсы:** CLI (`python -m rag.cli`) и HTTP API (FastAPI).

## Запуск

```bash
python -m venv .venv && .venv\Scripts\activate    # Windows
pip install -r requirements.txt
cp .env.example .env

docker compose up -d            # поднять Qdrant
python -m rag.cli ingest        # проиндексировать data/
python -m rag.cli ask "Делал ли кандидат RAG?"
```

HTTP API:

```bash
uvicorn rag.api:app --reload
# POST /ingest, POST /ask {"question": "..."}, GET /health
```

## Eval

Качество ретрива и ответов на отложенном датасете (`eval/dataset.jsonl`):

```bash
python -m eval.run_eval            # retrieval hit@k + latency
python -m eval.run_eval --answers  # + точность ответов по ключевым словам (через LLM)
```

## Тесты

```bash
pytest tests/
```

Тесты ретрива/генерации замоканы — сеть и LLM в unit-тестах не дёргаются.
