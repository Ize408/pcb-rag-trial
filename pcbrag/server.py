# uvicorn pcbrag.server:app --reload
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from pcbrag.assistant import Assistant

app = FastAPI(title="PCB doc assistant")
STATIC = Path(__file__).parent / "static"
_bot = None


def bot():
    global _bot
    if _bot is None:
        _bot = Assistant()
    return _bot


class Question(BaseModel):
    question: str
    history: list[list[str]] = []
    k: int | None = None


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    b = bot()
    return {"ok": True, "retriever": b.s.retriever, "llm": b.llm is not None}


@app.post("/api/ask")
def ask(q: Question):
    ans = bot().ask(q.question, k=q.k, history=[tuple(h) for h in q.history if len(h) == 2])
    return {
        "answer": ans.text,
        "used_llm": ans.used_llm,
        "sources": [{"n": i, "source": c.source, "where": c.header(), "type": c.doc_type,
                     "snippet": c.text[:400]} for i, c in enumerate(ans.sources, 1)],
    }


@app.get("/api/stats")
def stats():
    return {"stats": bot().log_stats()}
