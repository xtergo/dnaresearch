
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

app = FastAPI(title="DNA Research API (Monorepo Stub)")

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/genes/search")
def genes_search(query: str):
    return {"query": query, "hits": ["SHANK3","NRXN1","SYNGAP1"]}
