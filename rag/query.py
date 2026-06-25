import re

from .config import Config
from .llm import call_llm
from .store import Store

SOURCE_LABELS = {
    "about-me.md": "Обо мне",
    "skills.md": "Навыки",
    "projects-ai.md": "AI-проекты",
    "projects-prod.md": "Прод-проекты",
}

_CITE_RE = re.compile(r"\[([^\[\]]+?\.md)\]")


def _label(source):
    return SOURCE_LABELS.get(source, source)

PROMPT = """Ты отвечаешь на вопросы о профессиональном опыте кандидата строго по \
приведённым фрагментам документации. Если ответа в контексте нет — так и скажи, не \
выдумывай. Отвечай по-русски, кратко и по делу. В конце укажи источники в формате \
[источник].

Вопрос: {question}

Контекст:
{context}
"""


def build_context(hits):
    return "\n\n".join(
        f"[{h['source']}]\n{h['text']}" for h in hits
    )


def answer(question, cfg: Config = None, store=None):
    cfg = cfg or Config()
    store = store or Store(cfg)
    hits = store.search(question)
    if not hits:
        return {"answer": "В документации нет данных по этому вопросу.", "sources": []}
    prompt = PROMPT.format(question=question, context=build_context(hits))
    text = call_llm(prompt, engine=cfg.llm_engine)

    retrieved = {h["source"] for h in hits}
    cited = [s for s in dict.fromkeys(_CITE_RE.findall(text)) if s in retrieved]
    text = _CITE_RE.sub(
        lambda m: f"[{_label(m.group(1))}]" if m.group(1) in retrieved else m.group(0),
        text,
    )
    sources = [_label(s) for s in cited]
    return {"answer": text, "sources": sources, "hits": hits}
