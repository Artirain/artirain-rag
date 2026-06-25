from rag import query
from rag.config import Config


class FakeStore:
    def __init__(self, cfg):
        pass

    def search(self, question, top_k=None):
        return [
            {"score": 0.9, "text": "Стек: Python, Qdrant.", "source": "skills.md"},
            {"score": 0.8, "text": "RAG через retrieval.", "source": "projects-ai.md"},
        ]


class EmptyStore:
    def __init__(self, cfg):
        pass

    def search(self, question, top_k=None):
        return []


def test_answer_returns_only_cited_sources_as_labels(monkeypatch):
    captured = {}

    def fake_call(prompt, engine="codex"):
        captured["prompt"] = prompt
        captured["engine"] = engine
        return "Ответ. [skills.md]"

    monkeypatch.setattr(query, "Store", FakeStore)
    monkeypatch.setattr(query, "call_llm", fake_call)

    res = query.answer("Какой стек?", Config(llm_engine="codex"))

    # only the cited source, mapped to a human-readable label
    assert res["sources"] == ["Навыки"]
    assert "[Навыки]" in res["answer"]
    assert "Какой стек?" in captured["prompt"]
    assert "Стек: Python, Qdrant." in captured["prompt"]
    assert captured["engine"] == "codex"


def test_answer_ignores_uncited_and_hallucinated_sources(monkeypatch):
    def fake_call(prompt, engine="codex"):
        # cites one retrieved file and one that was never retrieved
        return "Текст [projects-ai.md] и [nonexistent.md]."

    monkeypatch.setattr(query, "Store", FakeStore)
    monkeypatch.setattr(query, "call_llm", fake_call)

    res = query.answer("вопрос", Config())

    assert res["sources"] == ["AI-проекты"]  # skills.md not cited, fake file dropped
    assert "[nonexistent.md]" in res["answer"]  # unknown citation left untouched


def test_answer_empty_retrieval_skips_llm(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("LLM must not be called when no hits")

    monkeypatch.setattr(query, "Store", EmptyStore)
    monkeypatch.setattr(query, "call_llm", boom)

    res = query.answer("Неизвестное", Config())
    assert res["sources"] == []
    assert "нет данных" in res["answer"].lower()
