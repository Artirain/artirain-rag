from fastapi import FastAPI
from pydantic import BaseModel

from .config import load_config
from .ingest import ingest
from .query import answer

app = FastAPI(title="rag-service")
cfg = load_config()


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok", "collection": cfg.collection, "engine": cfg.llm_engine}


@app.post("/ingest")
def do_ingest():
    n = ingest(cfg)
    return {"indexed_chunks": n}


@app.post("/ask")
def ask(req: AskRequest):
    res = answer(req.question, cfg)
    return {"answer": res["answer"], "sources": res["sources"]}
