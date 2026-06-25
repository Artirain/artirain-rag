from .config import Config
from .llm import call_llm
from .store import Store

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
    sources = sorted({h["source"] for h in hits})
    return {"answer": text, "sources": sources, "hits": hits}
