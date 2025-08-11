
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from datetime import datetime
from models import HealthResponse

app = FastAPI(
    title="DNA Research Platform API",
    description="Open, collaborative DNA research platform with privacy-preserving Bayesian analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0"
    )

@app.get("/genes/search")
def genes_search(query: str):
    return {"query": query, "hits": ["SHANK3","NRXN1","SYNGAP1"]}
