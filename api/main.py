
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI(title="DNA Research API (Monorepo Stub)")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
    }

@app.get("/genes/search")
def genes_search(query: str):
    return {"query": query, "hits": ["SHANK3","NRXN1","SYNGAP1"]}
