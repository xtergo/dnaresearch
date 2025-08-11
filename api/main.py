from datetime import datetime
from typing import Any, Dict, List

from anchor_diff import AnchorDiffStorage
from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from models import GenomicDataRequest, GenomicDataResponse, HealthResponse
from validators import validate_evidence, validate_theory

app = FastAPI(
    title="DNA Research Platform API",
    description="Open, collaborative DNA research platform with privacy-preserving Bayesian analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize storage
storage = AnchorDiffStorage()


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
        status="ok", timestamp=datetime.utcnow().isoformat() + "Z", version="1.0.0"
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
    return {"query": query, "hits": ["SHANK3", "NRXN1", "SYNGAP1"]}


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


@app.post("/evidence/validate")
def validate_evidence_endpoint(evidence: Dict[str, Any] = Body(...)):
    """
    Evidence Validation Endpoint

    Validate evidence JSON against the evidence schema.

    **Example Request:**
    ```json
    {
        "type": "variant_hit",
        "weight": 2.5,
        "timestamp": "2025-01-11T10:30:00Z",
        "data": {
            "gene": "SHANK3",
            "variant": "c.3679C>T",
            "impact": "high"
        }
    }
    ```
    """
    validated_evidence = validate_evidence(evidence)
    return {"status": "valid", "evidence": validated_evidence}


@app.post("/genomic/store", response_model=GenomicDataResponse)
def store_genomic_data(data: GenomicDataRequest):
    """
    Store Genomic Data with Anchor+Diff

    Efficiently store genomic data using anchor+diff compression.

    **Example Request:**
    ```json
    {
        "individual_id": "patient-001",
        "vcf_data": "#VCFV4.2\n1\t12345\t.\tA\tT\t60\tPASS",
        "reference_genome": "GRCh38"
    }
    ```
    """
    result = storage.process_genomic_data(
        individual_id=data.individual_id,
        vcf_data=data.vcf_data,
        reference_genome=data.reference_genome,
    )

    return GenomicDataResponse(**result)
