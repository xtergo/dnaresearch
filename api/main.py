
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from datetime import datetime
from models import HealthResponse
from validators import validate_theory
from typing import List, Dict, Any

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

@app.post("/theories/validate")
def validate_theory_endpoint(theory: Dict[str, Any] = Body(...)):
    """
    Theory Validation Endpoint
    
    Validate theory JSON against the theory schema.
    
    **Example Request:**
    ```json
    {
        "id": "autism-theory-1",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {"genes": ["SHANK3"]},
        "evidence_model": {"priors": 0.1, "likelihood_weights": {}}
    }
    ```
    """
    validated_theory = validate_theory(theory)
    return {"status": "valid", "theory": validated_theory}
