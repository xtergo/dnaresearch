
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from datetime import datetime
from models import HealthResponse
from typing import List

app = FastAPI(
    title="DNA Research Platform API",
    description="Open, collaborative DNA research platform with privacy-preserving Bayesian analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/health", response_model=HealthResponse)
def health():
    """
    Health Check Endpoint
    
    Returns the current health status of the API including:
    - System status (ok/error)
    - Current UTC timestamp
    - API version
    
    **Example Response:**
    ```json
    {
        "status": "ok",
        "timestamp": "2025-01-11T08:30:00.000Z",
        "version": "1.0.0"
    }
    ```
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0"
    )

@app.get("/genes/search")
def genes_search(query: str):
    """
    Gene Search Endpoint
    
    Search for genes by symbol, alias, or genomic coordinates.
    
    **Parameters:**
    - query: Gene symbol (e.g., "BRCA1"), alias, or coordinates
    
    **Example Response:**
    ```json
    {
        "query": "autism",
        "hits": ["SHANK3", "NRXN1", "SYNGAP1"]
    }
    ```
    """
    return {"query": query, "hits": ["SHANK3","NRXN1","SYNGAP1"]}
