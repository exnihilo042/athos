"""
ATHOS — agentmemory FastAPI wrapper.
Expose agentmemory (ChromaDB local) via REST sur :8765.
Lancé par agentmemory_server.py au boot ATHOS.
"""
import sys
from pathlib import Path

# Assurer que venv312 est dans le path
venv_site = Path(__file__).parent.parent / "venv312" / "lib" / "python3.12" / "site-packages"
if str(venv_site) not in sys.path:
    sys.path.insert(0, str(venv_site))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from agentmemory import (
    create_memory, get_memories, search_memory,
    delete_memory, count_memories, wipe_category,
)

app = FastAPI(title="ATHOS agentmemory API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modèles ───────────────────────────────────────────────────────────────────

class CreateMemoryRequest(BaseModel):
    category: str
    document: str
    metadata: Optional[dict] = None

class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = "athos"
    n_results: Optional[int] = 5

class MemoryOut(BaseModel):
    id: str
    document: str
    metadata: Optional[dict]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "agentmemory", "port": 8765}


@app.post("/memories", status_code=201)
def create(req: CreateMemoryRequest):
    meta = req.metadata or {}
    create_memory(req.category, req.document, metadata=meta)
    return {"status": "created", "category": req.category}


@app.get("/memories")
def list_memories(category: str = "athos", n_results: int = 20):
    mems = get_memories(category, n_results=n_results)
    return {"memories": mems, "count": len(mems)}


@app.post("/memories/search")
def search(req: SearchRequest):
    results = search_memory(
        req.query,
        req.category or "athos",
        n_results=req.n_results or 5,
    )
    return {"results": results, "count": len(results)}


@app.delete("/memories/{category}/{memory_id}")
def delete(category: str, memory_id: str):
    delete_memory(memory_id, category)
    return {"status": "deleted", "id": memory_id}


@app.get("/memories/count")
def count(category: str = "athos"):
    n = count_memories(category)
    return {"category": category, "count": n}


@app.delete("/memories/category/{category}")
def wipe(category: str):
    wipe_category(category)
    return {"status": "wiped", "category": category}


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="warning")
