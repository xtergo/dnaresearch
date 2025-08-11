from datetime import datetime
from typing import Any, Dict

from anchor_diff import AnchorDiffStorage
from evidence_accumulator import EvidenceAccumulator
from fastapi import Body, FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from gene_search import GeneSearchEngine
from models import GenomicDataRequest, GenomicDataResponse, HealthResponse
from sequence_materializer import SequenceMaterializer
from theory_engine import TheoryExecutionEngine
from theory_forker import TheoryForker
from validators import validate_evidence, validate_theory
from webhook_handler import WebhookHandler

app = FastAPI(
    title="DNA Research Platform API",
    description="Open, collaborative DNA research platform with "
    "privacy-preserving Bayesian analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize storage, materializer, theory engine, evidence accumulator, forker, gene search, and webhook handler
storage = AnchorDiffStorage()
materializer = SequenceMaterializer(storage)
theory_engine = TheoryExecutionEngine()
evidence_accumulator = EvidenceAccumulator()
theory_forker = TheoryForker()
gene_search = GeneSearchEngine()
webhook_handler = WebhookHandler()


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


@app.get("/genomic/stats/{individual_id}/{anchor_id}")
def get_materialization_stats(individual_id: str, anchor_id: str):
    """
    Get Materialization Statistics

    Get statistics about sequence materialization without full reconstruction.

    **Example Response:**
    ```json
    {
        "individual_id": "patient-001",
        "total_variants": 3,
        "sequence_length": 400,
        "materialization_efficiency": 0.0075
    }
    ```
    """
    stats = materializer.get_materialization_stats(individual_id, anchor_id)
    return stats


@app.get("/genes/search")
def genes_search(query: str, limit: int = 10):
    """
    Gene Search Endpoint

    Search for genes by symbol, alias, or genomic coordinates.

    **Parameters:**
    - query: Gene symbol (e.g., "BRCA1"), alias, or coordinates (e.g., "22:51150000-51180000")
    - limit: Maximum number of results to return (default: 10)

    **Example Response:**
    ```json
    {
        "query": "autism",
        "results": [
            {
                "symbol": "SHANK3",
                "name": "SH3 and multiple ankyrin repeat domains 3",
                "chromosome": "22",
                "location": "22:51150000-51180000",
                "description": "Critical for synaptic function and autism spectrum disorders",
                "match_type": "description"
            }
        ],
        "count": 1
    }
    ```
    """
    results = gene_search.search(query, limit)
    return {"query": query, "results": results, "count": len(results)}


@app.get("/genes/{symbol}")
def get_gene_details(symbol: str):
    """
    Get Gene Details

    Get detailed information about a specific gene by symbol.

    **Parameters:**
    - symbol: Gene symbol (e.g., "BRCA1")

    **Example Response:**
    ```json
    {
        "symbol": "BRCA1",
        "name": "BRCA1 DNA repair associated",
        "chromosome": "17",
        "location": "17:43044295-43125483",
        "aliases": ["BRCAI", "BRCC1"],
        "description": "Tumor suppressor gene involved in DNA repair and breast cancer",
        "pathways": ["dna_repair", "cancer_pathway"]
    }
    ```
    """
    gene = gene_search.get_gene_by_symbol(symbol)
    if not gene:
        raise HTTPException(status_code=404, detail=f"Gene '{symbol}' not found")
    return gene


@app.post("/webhooks/sequencing/{partner_id}")
def receive_webhook(
    partner_id: str,
    event_data: Dict[str, Any] = Body(...),
    x_signature: str = Header(None)
):
    """
    Sequencing Partner Webhook Endpoint

    Receive webhooks from sequencing partners for data processing updates.

    **Parameters:**
    - partner_id: Partner identifier (illumina, oxford, pacbio)
    - event_data: Webhook payload data
    - x_signature: Webhook signature for validation (optional)

    **Example Request:**
    ```json
    {
        "event_type": "sequencing_complete",
        "sample_id": "sample_001",
        "run_id": "run_20250111_001",
        "file_urls": [
            "https://partner.com/files/sample_001_R1.fastq.gz",
            "https://partner.com/files/sample_001_R2.fastq.gz"
        ],
        "metadata": {
            "instrument": "NovaSeq 6000",
            "run_date": "2025-01-11T10:00:00Z"
        }
    }
    ```

    **Example Response:**
    ```json
    {
        "status": "received",
        "event_id": "illumina_20250111_100000_123456",
        "partner_id": "illumina",
        "event_type": "sequencing_complete",
        "timestamp": "2025-01-11T10:00:00.000Z"
    }
    ```
    """
    try:
        # Validate signature if provided
        if x_signature:
            import json
            payload = json.dumps(event_data, sort_keys=True)
            if not webhook_handler.validate_signature(payload, x_signature, partner_id):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Process webhook
        event = webhook_handler.process_webhook(partner_id, event_data, x_signature)
        
        return {
            "status": event.status.value,
            "event_id": event.id,
            "partner_id": event.partner_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@app.get("/webhooks/events/{event_id}")
def get_webhook_event(event_id: str):
    """
    Get Webhook Event Details

    Retrieve details of a specific webhook event.

    **Parameters:**
    - event_id: Webhook event identifier

    **Example Response:**
    ```json
    {
        "id": "illumina_20250111_100000_123456",
        "partner_id": "illumina",
        "event_type": "sequencing_complete",
        "status": "completed",
        "timestamp": "2025-01-11T10:00:00.000Z",
        "data": {
            "sample_id": "sample_001",
            "processed_files": 2
        }
    }
    ```
    """
    event = webhook_handler.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
    
    return {
        "id": event.id,
        "partner_id": event.partner_id,
        "event_type": event.event_type,
        "status": event.status.value,
        "timestamp": event.timestamp,
        "data": event.data
    }


@app.get("/webhooks/partners/{partner_id}/events")
def get_partner_events(partner_id: str, limit: int = 50):
    """
    Get Partner Webhook Events

    Retrieve all webhook events for a specific partner.

    **Parameters:**
    - partner_id: Partner identifier
    - limit: Maximum number of events to return (default: 50)

    **Example Response:**
    ```json
    {
        "partner_id": "illumina",
        "events": [
            {
                "id": "illumina_20250111_100000_123456",
                "event_type": "sequencing_complete",
                "status": "completed",
                "timestamp": "2025-01-11T10:00:00.000Z"
            }
        ],
        "count": 1
    }
    ```
    """
    events = webhook_handler.get_partner_events(partner_id)
    
    # Limit and format results
    limited_events = events[:limit]
    formatted_events = [
        {
            "id": event.id,
            "event_type": event.event_type,
            "status": event.status.value,
            "timestamp": event.timestamp
        }
        for event in limited_events
    ]
    
    return {
        "partner_id": partner_id,
        "events": formatted_events,
        "count": len(formatted_events)
    }


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


@app.get("/genomic/materialize/{individual_id}/{anchor_id}")
def materialize_sequence(individual_id: str, anchor_id: str):
    """
    Materialize Genomic Sequence

    Reconstruct full genomic sequence from anchor+diff storage.

    **Parameters:**
    - individual_id: Individual identifier
    - anchor_id: Anchor sequence identifier

    **Example Response:**
    ```json
    {
        "individual_id": "patient-001",
        "sequence": "ATCGATCG...",
        "stats": {
            "total_variants": 3,
            "sequence_length": 400
        }
    }
    ```
    """
    try:
        sequence = materializer.materialize_sequence(individual_id, anchor_id)
        stats = materializer.get_materialization_stats(individual_id, anchor_id)

        return {
            "individual_id": individual_id,
            "anchor_id": anchor_id,
            "sequence": sequence,
            "stats": stats,
        }
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})


@app.post("/theories/{theory_id}/execute")
def execute_theory(
    theory_id: str,
    theory: Dict[str, Any] = Body(...),
    vcf_data: str = Body(..., embed=True),
    family_id: str = Body("default", embed=True),
):
    """
    Execute Theory Against VCF Data

    Execute a genomic theory against VCF data and calculate Bayes factors.

    **Parameters:**
    - theory_id: Theory identifier
    - theory: Complete theory JSON object
    - vcf_data: VCF format genomic data
    - family_id: Family/dataset identifier

    **Example Request:**
    ```json
    {
        "theory": {
            "id": "autism-theory-1",
            "version": "1.0.0",
            "scope": "autism",
            "criteria": {"genes": ["SHANK3"]},
            "evidence_model": {
                "priors": 0.1,
                "likelihood_weights": {"variant_hit": 2.0}
            }
        },
        "vcf_data": "#VCFV4.2\n22\t51150000\t.\tA\tT\t60\tPASS",
        "family_id": "family-001"
    }
    ```

    **Example Response:**
    ```json
    {
        "theory_id": "autism-theory-1",
        "version": "1.0.0",
        "bayes_factor": 2.5,
        "posterior": 0.2,
        "support_class": "moderate",
        "execution_time_ms": 150,
        "diagnostics": {
            "variants_analyzed": 1,
            "matching_genes": 1
        }
    }
    ```
    """
    try:
        # Validate theory first
        validated_theory = validate_theory(theory)

        # Check theory ID matches
        if validated_theory["id"] != theory_id:
            raise HTTPException(
                status_code=400,
                detail=f"Theory ID mismatch: {theory_id} vs "
                f"{validated_theory['id']}",
            )

        # Execute theory
        result = theory_engine.execute_theory(validated_theory, vcf_data, family_id)

        # Check execution time limit (30 seconds)
        if result.execution_time_ms > 30000:
            raise HTTPException(
                status_code=408,
                detail=f"Theory execution exceeded 30s limit: "
                f"{result.execution_time_ms}ms",
            )

        # Automatically add evidence from execution
        evidence_accumulator.add_evidence(
            theory_id=result.theory_id,
            theory_version=result.version,
            family_id=family_id,
            bayes_factor=result.bayes_factor,
            evidence_type="execution",
            weight=1.0,
            source="theory_execution",
        )

        return {
            "theory_id": result.theory_id,
            "version": result.version,
            "bayes_factor": result.bayes_factor,
            "posterior": result.posterior,
            "support_class": result.support_class,
            "execution_time_ms": result.execution_time_ms,
            "diagnostics": result.diagnostics,
            "artifact_hash": result.artifact_hash,
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Theory execution failed: {str(e)}"
        )


@app.post("/theories/{theory_id}/evidence")
def add_evidence(
    theory_id: str,
    theory_version: str = Body(..., embed=True),
    family_id: str = Body(..., embed=True),
    bayes_factor: float = Body(..., embed=True),
    evidence_type: str = Body("manual", embed=True),
    weight: float = Body(1.0, embed=True),
    source: str = Body("user_input", embed=True),
):
    """Add Evidence to Theory"""
    try:
        evidence_accumulator.add_evidence(
            theory_id=theory_id,
            theory_version=theory_version,
            family_id=family_id,
            bayes_factor=bayes_factor,
            evidence_type=evidence_type,
            weight=weight,
            source=source,
        )

        result = evidence_accumulator.update_posterior(theory_id, theory_version)

        return {
            "status": "evidence_added",
            "theory_id": result.theory_id,
            "version": result.version,
            "accumulated_bf": result.accumulated_bf,
            "posterior": result.posterior,
            "support_class": result.support_class,
            "evidence_count": result.evidence_count,
            "families_analyzed": result.families_analyzed,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add evidence: {str(e)}")


@app.get("/theories/{theory_id}/posterior")
def get_posterior(theory_id: str, theory_version: str, prior: float = 0.1):
    """Get Theory Posterior"""
    try:
        result = evidence_accumulator.update_posterior(theory_id, theory_version, prior)

        return {
            "theory_id": result.theory_id,
            "version": result.version,
            "prior": result.prior,
            "accumulated_bf": result.accumulated_bf,
            "posterior": result.posterior,
            "support_class": result.support_class,
            "evidence_count": result.evidence_count,
            "families_analyzed": result.families_analyzed,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get posterior: {str(e)}"
        )


@app.get("/theories/{theory_id}/evidence")
def get_evidence_trail(theory_id: str, theory_version: str):
    """Get Evidence Trail"""
    try:
        trail = evidence_accumulator.get_evidence_trail(theory_id, theory_version)

        return {
            "theory_id": theory_id,
            "version": theory_version,
            "evidence_trail": trail,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get evidence trail: {str(e)}"
        )


@app.post("/theories/{theory_id}/fork")
def fork_theory(
    theory_id: str,
    parent_theory: Dict[str, Any] = Body(...),
    new_theory_id: str = Body(..., embed=True),
    modifications: Dict[str, Any] = Body(..., embed=True),
    fork_reason: str = Body("user_modification", embed=True),
):
    """Fork Theory"""
    try:
        # Validate parent theory
        validated_parent = validate_theory(parent_theory)

        # Check parent theory ID matches
        if validated_parent["id"] != theory_id:
            raise HTTPException(
                status_code=400,
                detail=f"Parent theory ID mismatch: {theory_id} vs "
                f"{validated_parent['id']}",
            )

        # Fork the theory
        fork_result, new_theory = theory_forker.fork_theory(
            validated_parent, new_theory_id, modifications, fork_reason
        )

        # Validate the new theory
        validated_new_theory = validate_theory(new_theory)

        return {
            "status": "theory_forked",
            "new_theory_id": fork_result.new_theory_id,
            "new_version": fork_result.new_version,
            "parent_id": fork_result.parent_id,
            "parent_version": fork_result.parent_version,
            "changes_made": fork_result.changes_made,
            "new_theory": validated_new_theory,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fork theory: {str(e)}")


@app.get("/theories/{theory_id}/lineage")
def get_theory_lineage(theory_id: str, version: str):
    """Get Theory Lineage"""
    try:
        lineage = theory_forker.get_lineage(theory_id, version)

        if not lineage:
            return {
                "theory_id": theory_id,
                "version": version,
                "lineage": None,
                "is_root": True,
            }

        return {
            "theory_id": lineage.theory_id,
            "version": lineage.version,
            "parent_id": lineage.parent_id,
            "parent_version": lineage.parent_version,
            "fork_reason": lineage.fork_reason,
            "created_at": lineage.created_at,
            "is_root": False,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get lineage: {str(e)}")


@app.get("/theories/{theory_id}/children")
def get_theory_children(theory_id: str, version: str):
    """Get Theory Children"""
    try:
        children = theory_forker.get_children(theory_id, version)

        return {
            "parent_id": theory_id,
            "parent_version": version,
            "children": [
                {
                    "theory_id": child.theory_id,
                    "version": child.version,
                    "fork_reason": child.fork_reason,
                    "created_at": child.created_at,
                }
                for child in children
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get children: {str(e)}")


@app.get("/theories/{theory_id}/ancestry")
def get_theory_ancestry(theory_id: str, version: str):
    """Get Theory Ancestry"""
    try:
        ancestry = theory_forker.get_ancestry(theory_id, version)

        return {
            "theory_id": theory_id,
            "version": version,
            "ancestry": [
                {
                    "theory_id": ancestor.theory_id,
                    "version": ancestor.version,
                    "parent_id": ancestor.parent_id,
                    "parent_version": ancestor.parent_version,
                    "fork_reason": ancestor.fork_reason,
                    "created_at": ancestor.created_at,
                }
                for ancestor in ancestry
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ancestry: {str(e)}")
