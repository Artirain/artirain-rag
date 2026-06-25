from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .config import load_config
from .ingest import ingest
from .query import answer
from .ratelimit import RateLimiter
from .store import Store

app = FastAPI(title="rag-service")
cfg = load_config()
store = Store(cfg)
limiter = RateLimiter(cfg.rate_per_min, cfg.rate_per_day, cfg.global_per_day)


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.on_event("startup")
def _startup_ingest():
    # In embedded mode the corpus must be indexed into the live process at boot,
    # so the deployed demo is ready without a manual /ingest call.
    try:
        ingest(cfg, store)
    except Exception:
        pass


class AskRequest(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML


@app.get("/health")
def health():
    return {"status": "ok", "collection": cfg.collection, "engine": cfg.llm_engine}


@app.post("/ingest")
def do_ingest():
    n = ingest(cfg, store)
    return {"indexed_chunks": n}


@app.post("/ask")
def ask(req: AskRequest, request: Request):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="empty question")
    if len(question) > cfg.max_question_chars:
        raise HTTPException(status_code=400, detail="question too long")
    reason = limiter.check(_client_ip(request))
    if reason:
        raise HTTPException(status_code=429, detail=reason)
    res = answer(question, cfg, store)
    return {"answer": res["answer"], "sources": res["sources"]}


INDEX_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RAG по опыту кандидата — спросите что угодно</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: "Segoe UI", system-ui, sans-serif; background: #0f1623;
         color: #e6ebf3; display: flex; justify-content: center; padding: 32px 16px; }
  .wrap { width: 100%; max-width: 720px; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  .sub { color: #8b97ad; font-size: 14px; margin-bottom: 20px; }
  .ask { display: flex; gap: 8px; }
  input { flex: 1; padding: 12px 14px; border-radius: 10px; border: 1px solid #2a3650;
          background: #182338; color: #e6ebf3; font-size: 15px; }
  input:focus { outline: none; border-color: #4a6fa5; }
  button { padding: 12px 18px; border: none; border-radius: 10px; background: #4a6fa5;
           color: #fff; font-size: 15px; font-weight: 600; cursor: pointer; }
  button:disabled { opacity: .5; cursor: default; }
  .chips { margin: 14px 0 0; display: flex; flex-wrap: wrap; gap: 8px; }
  .chip { font-size: 13px; color: #aebbd2; background: #182338; border: 1px solid #2a3650;
          padding: 6px 10px; border-radius: 999px; cursor: pointer; }
  .chip:hover { border-color: #4a6fa5; }
  .answer { margin-top: 22px; background: #182338; border: 1px solid #2a3650;
            border-radius: 12px; padding: 18px 20px; line-height: 1.55; white-space: pre-wrap;
            display: none; }
  .answer.show { display: block; }
  .src { margin-top: 12px; font-size: 12.5px; color: #8b97ad; }
  .foot { margin-top: 26px; font-size: 12px; color: #5e6b82; }
  a { color: #7fa6df; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Спросите про опыт кандидата</h1>
  <div class="sub">RAG поверх документации портфолио. Ответы строятся только по документам, с указанием источников.</div>
  <div class="ask">
    <input id="q" placeholder="Например: делал ли кандидат RAG?" autocomplete="off">
    <button id="go">Спросить</button>
  </div>
  <div class="chips" id="chips"></div>
  <div class="answer" id="answer"></div>
  <div class="foot">Движок: Gemini · векторный поиск Qdrant + fastembed · grounded, без выдумок.</div>
</div>
<script>
const examples = [
  "Делал ли кандидат RAG и на каком стеке?",
  "Есть ли опыт с Kubernetes и CI/CD?",
  "Какие проекты связаны с платежами?",
  "Как кандидат относится к тестированию?",
];
const chips = document.getElementById("chips");
examples.forEach(t => {
  const c = document.createElement("span");
  c.className = "chip"; c.textContent = t;
  c.onclick = () => { document.getElementById("q").value = t; ask(); };
  chips.appendChild(c);
});
const ansEl = document.getElementById("answer");
const btn = document.getElementById("go");
async function ask() {
  const q = document.getElementById("q").value.trim();
  if (!q) return;
  btn.disabled = true;
  ansEl.className = "answer show";
  ansEl.textContent = "Думаю…";
  try {
    const r = await fetch("/ask", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({question: q})
    });
    const data = await r.json();
    if (!r.ok) {
      ansEl.textContent = data.detail === "too many requests, please slow down"
        ? "Слишком много запросов — подождите минуту."
        : (data.detail === "daily limit per visitor reached" || data.detail === "daily budget reached, try again tomorrow")
        ? "Достигнут дневной лимит запросов. Загляните завтра."
        : "Запрос отклонён: " + (data.detail || "ошибка");
      return;
    }
    ansEl.innerHTML = "";
    const a = document.createElement("div");
    a.textContent = data.answer || "Нет ответа.";
    ansEl.appendChild(a);
    if (data.sources && data.sources.length) {
      const s = document.createElement("div");
      s.className = "src";
      s.textContent = "Источники: " + data.sources.join(", ");
      ansEl.appendChild(s);
    }
  } catch (e) {
    ansEl.textContent = "Ошибка запроса. Попробуйте ещё раз.";
  } finally {
    btn.disabled = false;
  }
}
btn.onclick = ask;
document.getElementById("q").addEventListener("keydown", e => { if (e.key === "Enter") ask(); });
</script>
</body>
</html>
"""
