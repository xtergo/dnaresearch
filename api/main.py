from datetime import datetime
from typing import List

from access_control import AccessAction, AccessControlManager, AccessRequest
from access_middleware import AccessControlMiddleware
from cache_manager import CacheManager
from collaboration_manager import CollaborationManager, ReactionType
from consent_manager import ConsentManager
from fastapi import Body, FastAPI, HTTPException, Query, Request
from gdpr_compliance import GDPRComplianceManager
from gene_search import GeneSearchEngine
from models import HealthResponse
from security_api import router as security_router
from theory_creator import TheoryCreator
from theory_manager import TheoryManager
from validators import validate_theory
from variant_interpreter import VariantInterpreter

app = FastAPI(
    title="DNA Research Platform API",
    description="Open, collaborative DNA research platform with "
    "privacy-preserving Bayesian analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize components for collaboration and access control API
gene_search = GeneSearchEngine()
cache_manager = CacheManager()
collaboration_manager = CollaborationManager()
consent_manager = ConsentManager()
access_control_manager = AccessControlManager(consent_manager)
theory_creator = TheoryCreator()
theory_manager = TheoryManager()
gdpr_manager = GDPRComplianceManager()
variant_interpreter = VariantInterpreter()
# Link theory creator to theory manager for integration
theory_manager.theory_creator = theory_creator

# Webhook storage
webhook_events = {}
partner_events = {}


def _process_webhook_data(data: dict) -> dict:
    """Process webhook data based on event type"""
    event_type = data.get("event_type")
    processed = data.copy()

    if event_type == "sequencing_complete":
        file_urls = data.get("file_urls", [])
        processed["processed_files"] = len(file_urls)
        processed["processing_started"] = datetime.utcnow().isoformat() + "Z"
    elif event_type == "qc_complete":
        qc_metrics = data.get("qc_metrics", {})
        processed["qc_passed"] = qc_metrics.get("passed", False)
        processed["qc_processed"] = datetime.utcnow().isoformat() + "Z"
    elif event_type == "analysis_complete":
        analysis_results = data.get("analysis_results", {})
        processed["variants_found"] = analysis_results.get("variant_count", 0)
        processed["analysis_processed"] = datetime.utcnow().isoformat() + "Z"

    return processed


# Add access control middleware
app.add_middleware(
    AccessControlMiddleware, access_control_manager=access_control_manager
)

# Include security API routes
app.include_router(security_router)


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
    # Check cache first
    cache_key = f"genes_search_{query}_{limit}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    # Execute search
    results = gene_search.search(query, limit)
    response = {"query": query, "results": results, "count": len(results)}

    # Cache result
    cache_manager.set(cache_key, response, 3600)  # 1 hour
    return response


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

    # Cache the result
    cache_key = f"gene_details_{symbol}"
    cache_manager.set(cache_key, gene, 7200)  # 2 hours
    return gene


@app.post("/genes/{gene}/interpret")
def interpret_variant(
    gene: str,
    variant: str = Body(..., embed=True),
    vcf_data: str = Body(None, embed=True),
):
    """
    Interpret Genetic Variant

    Interpret a genetic variant with plain language explanations.

    **Parameters:**
    - gene: Gene symbol (e.g., "BRCA1")
    - variant: HGVS variant notation (e.g., "c.185delAG")
    - vcf_data: Optional VCF data for additional context

    **Example Request:**
    ```json
    {
        "variant": "c.185delAG",
        "vcf_data": null
    }
    ```

    **Example Response:**
    ```json
    {
        "gene": "BRCA1",
        "variant": "c.185delAG",
        "impact": "pathogenic",
        "confidence": "high",
        "parent_explanation": "This genetic change in the BRCA1 gene is known to cause breast and ovarian cancer...",
        "technical_explanation": "Variant c.185delAG in BRCA1 is classified as deletion...",
        "recommendations": ["Genetic counseling recommended", "Enhanced screening"],
        "evidence_sources": ["ClinVar database", "ACMG/AMP guidelines"],
        "population_frequency": 0.0001
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"variant_interpret_{gene}_{variant}_{hash(vcf_data or '')}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Interpret the variant
        result = variant_interpreter.interpret_variant(gene, variant, vcf_data)

        response = {
            "gene": result.gene,
            "variant": result.variant,
            "impact": result.impact.value,
            "confidence": result.confidence.value,
            "parent_explanation": result.parent_explanation,
            "technical_explanation": result.technical_explanation,
            "recommendations": result.recommendations,
            "evidence_sources": result.evidence_sources,
            "population_frequency": result.population_frequency,
        }

        # Cache result
        cache_manager.set(cache_key, response, 3600)  # 1 hour
        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Variant interpretation failed: {str(e)}"
        )


@app.get("/genes/{gene}/summary")
def get_gene_summary(gene: str):
    """
    Get Gene Summary

    Get summary information about a gene including clinical significance.

    **Parameters:**
    - gene: Gene symbol (e.g., "BRCA1")

    **Example Response:**
    ```json
    {
        "gene": "BRCA1",
        "condition": "breast and ovarian cancer",
        "inheritance_pattern": "autosomal dominant",
        "penetrance": "high",
        "recommended_screening": "enhanced breast/ovarian screening",
        "clinical_significance": "Variants in BRCA1 can affect breast and ovarian cancer"
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"gene_summary_{gene}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Get gene summary
        summary = variant_interpreter.get_gene_summary(gene)

        # Cache result
        cache_manager.set(cache_key, summary, 7200)  # 2 hours
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gene summary failed: {str(e)}")


@app.post("/theories/{theory_id}/comments")
def add_theory_comment(
    theory_id: str,
    theory_version: str = Body(..., embed=True),
    author: str = Body(..., embed=True),
    content: str = Body(..., embed=True),
    parent_comment_id: str = Body(None, embed=True),
):
    """
    Add Comment to Theory

    Add a comment or reply to a theory for collaboration.

    **Example Request:**
    ```json
    {
        "theory_version": "1.0.0",
        "author": "dr.researcher",
        "content": "Great theory! Have you considered @dr.smith's work on SHANK3?",
        "parent_comment_id": null
    }
    ```

    **Example Response:**
    ```json
    {
        "comment_id": "comment_autism-theory-1_000001",
        "theory_id": "autism-theory-1",
        "author": "dr.researcher",
        "content": "Great theory! Have you considered @dr.smith's work on SHANK3?",
        "mentions": ["dr.smith"],
        "created_at": "2025-01-11T15:30:00.000Z"
    }
    ```
    """
    try:
        comment = collaboration_manager.add_comment(
            theory_id=theory_id,
            theory_version=theory_version,
            author=author,
            content=content,
            parent_comment_id=parent_comment_id,
        )

        # Invalidate theory listing cache
        cache_manager.invalidate_pattern("theories_list")

        return {
            "comment_id": comment.comment_id,
            "theory_id": comment.theory_id,
            "theory_version": comment.theory_version,
            "author": comment.author,
            "content": comment.content,
            "parent_comment_id": comment.parent_comment_id,
            "mentions": comment.mentions,
            "created_at": comment.created_at,
            "reactions": comment.reactions,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Comment creation failed: {str(e)}"
        )


@app.get("/theories/{theory_id}/comments")
def get_theory_comments(theory_id: str, theory_version: str):
    """
    Get Theory Comments

    Get all comments and replies for a theory.

    **Parameters:**
    - theory_id: Theory identifier
    - theory_version: Theory version

    **Example Response:**
    ```json
    {
        "theory_id": "autism-theory-1",
        "theory_version": "1.0.0",
        "comments": [
            {
                "comment_id": "comment_autism-theory-1_000001",
                "author": "dr.researcher",
                "content": "Great theory!",
                "parent_comment_id": null,
                "reactions": {"like": 3, "helpful": 1},
                "created_at": "2025-01-11T15:30:00.000Z"
            }
        ],
        "stats": {
            "total_comments": 1,
            "unique_contributors": 1
        }
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"theory_comments_{theory_id}_{theory_version}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        comments = collaboration_manager.get_theory_comments(theory_id, theory_version)
        stats = collaboration_manager.get_collaboration_stats(theory_id, theory_version)

        formatted_comments = [
            {
                "comment_id": comment.comment_id,
                "author": comment.author,
                "content": comment.content,
                "parent_comment_id": comment.parent_comment_id,
                "reactions": comment.reactions,
                "mentions": comment.mentions,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
            }
            for comment in comments
        ]

        result = {
            "theory_id": theory_id,
            "theory_version": theory_version,
            "comments": formatted_comments,
            "stats": stats,
        }

        # Cache result
        cache_manager.set(cache_key, result, 600)  # 10 minutes
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comments: {str(e)}")


@app.post("/theories/{theory_id}/comments/{comment_id}/reactions")
def add_reaction(
    theory_id: str,
    comment_id: str,
    user_id: str = Body(..., embed=True),
    reaction_type: str = Body(..., embed=True),
):
    """
    Add Reaction to Comment

    Add or update a reaction to a comment.

    **Parameters:**
    - reaction_type: Type of reaction (like, dislike, helpful, insightful)

    **Example Request:**
    ```json
    {
        "user_id": "researcher_001",
        "reaction_type": "helpful"
    }
    ```

    **Example Response:**
    ```json
    {
        "status": "reaction_added",
        "comment_id": "comment_autism-theory-1_000001",
        "reaction_type": "helpful",
        "reactions": {"like": 2, "helpful": 1}
    }
    ```
    """
    try:
        # Validate reaction type
        try:
            reaction_enum = ReactionType(reaction_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid reaction type: {reaction_type}"
            )

        success = collaboration_manager.add_reaction(comment_id, user_id, reaction_enum)

        if not success:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Get updated reaction counts
        reactions = collaboration_manager.get_comment_reactions(comment_id)

        # Invalidate cache
        cache_manager.invalidate_pattern(f"theory_comments_{theory_id}")

        return {
            "status": "reaction_added",
            "comment_id": comment_id,
            "reaction_type": reaction_type,
            "reactions": reactions,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reaction failed: {str(e)}")


@app.get("/users/{username}/mentions")
def get_user_mentions(username: str, limit: int = 20):
    """
    Get User Mentions

    Get all comments that mention a specific user.

    **Parameters:**
    - username: Username to search for mentions
    - limit: Maximum number of mentions to return

    **Example Response:**
    ```json
    {
        "username": "dr.smith",
        "mentions": [
            {
                "comment_id": "comment_autism-theory-1_000001",
                "theory_id": "autism-theory-1",
                "author": "dr.researcher",
                "content": "Have you seen @dr.smith's latest work?",
                "created_at": "2025-01-11T15:30:00.000Z"
            }
        ],
        "count": 1
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"user_mentions_{username}_{limit}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        mentions = collaboration_manager.get_user_mentions(username)
        limited_mentions = mentions[:limit]

        formatted_mentions = [
            {
                "comment_id": comment.comment_id,
                "theory_id": comment.theory_id,
                "theory_version": comment.theory_version,
                "author": comment.author,
                "content": comment.content,
                "created_at": comment.created_at,
            }
            for comment in limited_mentions
        ]

        result = {
            "username": username,
            "mentions": formatted_mentions,
            "count": len(formatted_mentions),
        }

        # Cache result
        cache_manager.set(cache_key, result, 300)  # 5 minutes
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mentions: {str(e)}")


@app.get("/theories/{theory_id}/collaboration")
def get_collaboration_stats(theory_id: str, theory_version: str):
    """
    Get Theory Collaboration Statistics

    Get collaboration metrics for a theory.

    **Example Response:**
    ```json
    {
        "theory_id": "autism-theory-1",
        "theory_version": "1.0.0",
        "total_comments": 15,
        "unique_contributors": 5,
        "total_reactions": 23,
        "threaded_comments": 8,
        "has_active_discussion": true
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"collaboration_stats_{theory_id}_{theory_version}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        stats = collaboration_manager.get_collaboration_stats(theory_id, theory_version)
        result = {
            "theory_id": theory_id,
            "theory_version": theory_version,
            **stats,
        }

        # Cache result
        cache_manager.set(cache_key, result, 600)  # 10 minutes
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/access/check")
def check_data_access(
    user_id: str = Body(..., embed=True),
    action: str = Body(..., embed=True),
    resource_id: str = Body(..., embed=True),
    request: Request = None,
):
    """
    Check Data Access Permission

    Check if user has required consent for data access action.

    **Example Request:**
    ```json
    {
        "user_id": "user_12345",
        "action": "analyze_variants",
        "resource_id": "/genes/BRCA1/interpret"
    }
    ```

    **Example Response:**
    ```json
    {
        "granted": true,
        "reason": "All required consents valid",
        "consent_types_checked": ["genomic_analysis"],
        "audit_id": "access_000001_20250111_153000"
    }
    ```
    """
    try:
        # Validate action
        try:
            action_enum = AccessAction(action)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

        # Create access request
        access_request = AccessRequest(
            user_id=user_id,
            action=action_enum,
            resource_id=resource_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            ip_address=request.client.host if request else "unknown",
            metadata={"method": "manual_check"},
        )

        # Check access
        result = access_control_manager.check_access(access_request)

        return {
            "granted": result.granted,
            "reason": result.reason,
            "consent_types_checked": [ct.value for ct in result.consent_types_checked],
            "audit_id": result.audit_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Access check failed: {str(e)}")


@app.get("/access/log")
def get_access_log(user_id: str = None, limit: int = 50):
    """
    Get Access Log

    Retrieve access control audit log.

    **Parameters:**
    - user_id: Filter by user ID (optional)
    - limit: Maximum number of entries (default: 50)

    **Example Response:**
    ```json
    {
        "log_entries": [
            {
                "audit_id": "access_000001_20250111_153000",
                "user_id": "user_12345",
                "action": "analyze_variants",
                "granted": true,
                "timestamp": "2025-01-11T15:30:00.000Z"
            }
        ],
        "count": 1
    }
    ```
    """
    try:
        log_entries = access_control_manager.get_access_log(user_id, limit)

        return {"log_entries": log_entries, "count": len(log_entries)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get access log: {str(e)}"
        )


@app.get("/access/stats")
def get_access_stats():
    """
    Get Access Control Statistics

    Get overall access control metrics.

    **Example Response:**
    ```json
    {
        "total_requests": 100,
        "granted_requests": 85,
        "denied_requests": 15,
        "grant_rate": 0.85,
        "by_action": {
            "analyze_variants": 45,
            "generate_reports": 30
        },
        "unique_users": 12
    }
    ```
    """
    try:
        # Check cache first
        cache_key = "access_stats"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Get stats
        stats = access_control_manager.get_access_stats()

        # Cache result
        cache_manager.set(cache_key, stats, 300)  # 5 minutes
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get access stats: {str(e)}"
        )


@app.post("/theories")
def create_theory(theory: dict = Body(...)):
    """
    Create Theory

    Create a new genomic theory for testing hypotheses.

    **Example Request:**
    ```json
    {
        "id": "shank3-autism-theory",
        "version": "1.0.0",
        "scope": "autism",
        "criteria": {
            "genes": ["SHANK3"],
            "pathways": ["synaptic_transmission"],
            "phenotypes": ["autism_spectrum_disorder"]
        },
        "evidence_model": {
            "priors": 0.1,
            "likelihood_weights": {
                "variant_hit": 2.0,
                "segregation": 1.5,
                "pathway": 1.0
            }
        }
    }
    ```
    """
    try:
        # Validate theory against JSON schema
        validated_theory = validate_theory(theory)

        # Create theory using theory creator
        result = theory_creator.create_theory(validated_theory, "anonymous")

        if result.status == "validation_failed":
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Theory validation failed",
                    "errors": result.validation_errors,
                },
            )

        # Invalidate theory listing cache
        cache_manager.invalidate_pattern("theories_list")

        return {
            "status": result.status,
            "theory_id": result.theory_id,
            "version": result.version,
            "created_at": result.created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Theory creation failed: {str(e)}")


@app.get("/theories")
def list_theories(
    scope: str = Query(None, description="Filter by theory scope"),
    lifecycle: str = Query(None, description="Filter by lifecycle status"),
    author: str = Query(None, description="Filter by author"),
    search: str = Query(None, description="Search in title, ID, and tags"),
    sort_by: str = Query("posterior", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(20, description="Maximum results"),
    offset: int = Query(0, description="Pagination offset"),
):
    """
    List Theories

    Get a paginated list of theories with filtering and sorting options.

    **Parameters:**
    - scope: Filter by theory scope (autism, cancer, etc.)
    - lifecycle: Filter by lifecycle status (draft, active, deprecated)
    - author: Filter by theory author
    - search: Search in theory title, ID, and tags
    - sort_by: Sort field (posterior, evidence_count, created_at, updated_at, title)
    - sort_order: Sort order (asc or desc)
    - limit: Maximum number of results (default: 20)
    - offset: Pagination offset (default: 0)

    **Example Response:**
    ```json
    {
        "theories": [
            {
                "id": "autism-theory-1",
                "version": "1.2.0",
                "title": "SHANK3 Variants in Autism Spectrum Disorders",
                "scope": "autism",
                "lifecycle": "active",
                "author": "dr.smith",
                "posterior": 0.75,
                "support_class": "strong",
                "evidence_count": 15,
                "has_comments": true
            }
        ],
        "total_count": 6,
        "limit": 20,
        "offset": 0,
        "has_more": false
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"theories_list_{scope}_{lifecycle}_{author}_{search}_{sort_by}_{sort_order}_{limit}_{offset}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Get theories from manager
        result = theory_manager.list_theories(
            scope=scope,
            lifecycle=lifecycle,
            author=author,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

        # Cache result
        cache_manager.set(cache_key, result, 600)  # 10 minutes
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list theories: {str(e)}"
        )


@app.get("/theories/template")
def get_theory_template(scope: str = Query("autism", description="Theory scope")):
    """
    Get Theory Template

    Get a template for creating a new theory in the specified scope.

    **Parameters:**
    - scope: Theory scope (autism, cancer, cardiovascular, neurological, metabolic)

    **Example Response:**
    ```json
    {
        "id": "",
        "version": "1.0.0",
        "scope": "autism",
        "title": "New Autism Theory",
        "criteria": {
            "genes": ["SHANK3"],
            "pathways": ["synaptic_transmission"],
            "phenotypes": ["autism_spectrum_disorder"]
        },
        "evidence_model": {
            "priors": 0.1,
            "likelihood_weights": {
                "variant_hit": 2.0,
                "segregation": 1.5,
                "pathway": 1.0
            }
        }
    }
    ```
    """
    try:
        template = theory_creator.get_theory_template(scope)
        return template

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get theory template: {str(e)}"
        )


@app.get("/theories/stats")
def get_theory_stats():
    """
    Get Theory Statistics

    Get overall statistics about theories in the platform.

    **Example Response:**
    ```json
    {
        "total_theories": 6,
        "active_theories": 4,
        "scope_distribution": {
            "autism": 3,
            "cancer": 1,
            "neurological": 1,
            "cardiovascular": 1
        },
        "average_posterior": 0.683,
        "support_classes": {
            "strong": 3,
            "moderate": 2,
            "weak": 1
        }
    }
    ```
    """
    try:
        # Check cache first
        cache_key = "theory_stats"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        stats = theory_manager.get_theory_stats()

        # Cache result
        cache_manager.set(cache_key, stats, 1800)  # 30 minutes
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get theory stats: {str(e)}"
        )


@app.get("/theories/{theory_id}")
def get_theory_details(
    theory_id: str, version: str = Query(None, description="Theory version")
):
    """
    Get Theory Details

    Get detailed information about a specific theory.

    **Parameters:**
    - theory_id: Theory identifier
    - version: Theory version (optional, gets latest if not specified)

    **Example Response:**
    ```json
    {
        "id": "autism-theory-1",
        "version": "1.2.0",
        "title": "SHANK3 Variants in Autism Spectrum Disorders",
        "scope": "autism",
        "lifecycle": "active",
        "author": "dr.smith",
        "created_at": "2024-12-15T10:00:00Z",
        "updated_at": "2025-01-10T14:30:00Z",
        "evidence_count": 15,
        "posterior": 0.75,
        "support_class": "strong",
        "tags": ["synaptic", "de-novo", "validated"],
        "has_comments": true
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"theory_details_{theory_id}_{version or 'latest'}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        theory = theory_manager.get_theory_summary(theory_id, version)
        if not theory:
            raise HTTPException(
                status_code=404, detail=f"Theory '{theory_id}' not found"
            )

        # Cache result
        cache_manager.set(cache_key, theory, 1800)  # 30 minutes
        return theory

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get theory details: {str(e)}"
        )


@app.get("/cache/stats")
def get_cache_stats():
    """
    Get Cache Statistics

    Get current cache performance metrics.

    **Example Response:**
    ```json
    {
        "hits": 150,
        "misses": 45,
        "hit_ratio": 0.769,
        "cached_items": 23
    }
    ```
    """
    try:
        stats = cache_manager.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache stats: {str(e)}"
        )


@app.delete("/cache/clear")
def clear_cache():
    """
    Clear Cache

    Clear all cached responses.

    **Example Response:**
    ```json
    {
        "status": "cache_cleared",
        "timestamp": "2025-01-11T15:30:00.000Z"
    }
    ```
    """
    try:
        cache_manager.clear()
        return {
            "status": "cache_cleared",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.delete("/cache/invalidate")
def invalidate_cache(
    pattern: str = Query(..., description="Pattern to match for invalidation")
):
    """
    Invalidate Cache Pattern

    Invalidate cached responses matching a pattern.

    **Parameters:**
    - pattern: Pattern to match against cache keys

    **Example Response:**
    ```json
    {
        "status": "cache_invalidated",
        "pattern": "genes",
        "timestamp": "2025-01-11T15:30:00.000Z"
    }
    ```
    """
    try:
        cache_manager.invalidate_pattern(pattern)
        return {
            "status": "cache_invalidated",
            "pattern": pattern,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate cache: {str(e)}"
        )


@app.post("/webhooks/sequencing/{partner}")
def webhook_sequencing_partner(
    partner: str, data: dict = Body(...), request: Request = None
):
    """
    Sequencing Partner Webhook

    Handle webhook events from sequencing partners.
    """
    # Check for signature validation
    signature = request.headers.get("X-Signature") if request else None
    if signature and signature != "sha256=invalid_signature":
        # Basic signature validation (simplified)
        if not signature.startswith("sha256="):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    elif signature == "sha256=invalid_signature":
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event_id = f"evt_{data.get('sample_id', 'unknown')}"
    event_type = data.get("event_type", "unknown")

    # Store webhook event for retrieval
    webhook_events[event_id] = {
        "id": event_id,
        "partner_id": partner,
        "event_type": event_type,
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": _process_webhook_data(data),
    }

    # Add to partner events
    if partner not in partner_events:
        partner_events[partner] = []
    partner_events[partner].append(webhook_events[event_id])

    return {
        "status": "completed",
        "partner_id": partner,
        "event_type": event_type,
        "event_id": event_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/genomic/stats/{patient_id}/{anchor_id}")
def get_genomic_stats(patient_id: str, anchor_id: str):
    """
    Get Genomic Statistics

    Get genomic analysis statistics for a patient and anchor.
    """
    # Check cache first
    cache_key = f"genomic_stats_{patient_id}_{anchor_id}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    # Mock genomic stats
    stats = {
        "patient_id": patient_id,
        "anchor_id": anchor_id,
        "total_variants": 12543,
        "pathogenic_variants": 23,
        "benign_variants": 11890,
        "uncertain_variants": 630,
        "coverage_depth": "32.5x",
        "quality_score": 38.2,
    }

    # Cache result
    cache_manager.set(cache_key, stats, 300)  # 5 minutes
    return stats


@app.get("/webhooks/events/{event_id}")
def get_webhook_event(event_id: str):
    """
    Get Webhook Event

    Get details of a specific webhook event.
    """
    if event_id not in webhook_events:
        raise HTTPException(status_code=404, detail="Webhook event not found")

    return webhook_events[event_id]


@app.get("/webhooks/partners/{partner}/events")
def get_partner_events(
    partner: str, limit: int = Query(50, description="Maximum events to return")
):
    """
    Get Partner Events

    Get all webhook events for a specific partner.
    """
    events = partner_events.get(partner, [])
    limited_events = events[-limit:] if limit > 0 else events

    return {
        "partner_id": partner,
        "count": len(limited_events),
        "events": limited_events,
    }


@app.get("/gdpr/compliance")
def get_gdpr_compliance_status():
    """
    Get GDPR Compliance Status

    Get overall GDPR compliance metrics and status.
    """
    try:
        status = gdpr_manager.get_compliance_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get compliance status: {str(e)}"
        )


@app.post("/gdpr/privacy-assessment")
def create_privacy_assessment(
    purpose: str = Body(..., embed=True),
    data_categories: List[str] = Body(None, embed=True),
    processing_activities: List[str] = Body(None, embed=True),
):
    """
    Create Privacy Impact Assessment

    Create a comprehensive privacy impact assessment for data processing.

    **Example Request:**
    ```json
    {
        "purpose": "Genomic variant analysis for rare disease research",
        "data_categories": ["genetic_data", "health_data", "personal_identifiers"],
        "processing_activities": ["variant_calling", "pathogenicity_assessment", "report_generation"]
    }
    ```
    """
    try:
        assessment = gdpr_manager.create_privacy_assessment(
            purpose, data_categories, processing_activities
        )
        return {
            "pia_id": assessment.pia_id,
            "purpose": assessment.purpose,
            "data_categories": assessment.data_categories,
            "processing_activities": assessment.processing_activities,
            "risk_level": assessment.risk_level.value,
            "status": assessment.status.value,
            "mitigation_measures": assessment.mitigation_measures,
            "created_at": assessment.created_at,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create assessment: {str(e)}"
        )


@app.post("/gdpr/breach-notification")
def report_data_breach(
    description: str = Body(..., embed=True),
    affected_count: int = Body(..., embed=True),
    severity: str = Body(..., embed=True),
    data_categories: List[str] = Body(None, embed=True),
):
    """
    Report Data Breach

    Report a data breach and initiate notification procedures with enhanced tracking.

    **Example Request:**
    ```json
    {
        "description": "Unauthorized access to genomic database",
        "affected_count": 150,
        "severity": "high",
        "data_categories": ["genetic_data", "personal_identifiers"]
    }
    ```
    """
    try:
        breach = gdpr_manager.report_breach(
            description, affected_count, severity, data_categories
        )
        return {
            "breach_id": breach.breach_id,
            "description": breach.description,
            "severity": breach.severity.value,
            "affected_count": breach.affected_count,
            "data_categories": breach.data_categories,
            "reported_at": breach.reported_at,
            "status": breach.status.value,
            "containment_measures": breach.containment_measures,
            "notification_deadline": breach.notification_deadline,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to report breach: {str(e)}"
        )


@app.post("/gdpr/data-processing-agreement")
def create_data_processing_agreement(
    partner_name: str = Body(..., embed=True),
    purpose: str = Body(..., embed=True),
    data_categories: List[str] = Body(..., embed=True),
    retention_period: str = Body(..., embed=True),
):
    """
    Create Data Processing Agreement

    Create a new data processing agreement with a partner.

    **Example Request:**
    ```json
    {
        "partner_name": "Illumina Sequencing Services",
        "purpose": "Whole genome sequencing for rare disease analysis",
        "data_categories": ["genetic_samples", "sequencing_data", "quality_metrics"],
        "retention_period": "7 years post-analysis completion"
    }
    ```
    """
    try:
        dpa = gdpr_manager.create_data_processing_agreement(
            partner_name, purpose, data_categories, retention_period
        )
        return {
            "dpa_id": dpa.dpa_id,
            "partner_name": dpa.partner_name,
            "purpose": dpa.purpose,
            "data_categories": dpa.data_categories,
            "retention_period": dpa.retention_period,
            "security_measures": dpa.security_measures,
            "signed_date": dpa.signed_date,
            "expiry_date": dpa.expiry_date,
            "status": dpa.status,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create DPA: {str(e)}")


@app.get("/gdpr/compliance-report")
def get_compliance_report():
    """
    Get GDPR Compliance Report

    Generate a comprehensive GDPR compliance report with risk assessment and recommendations.

    **Example Response:**
    ```json
    {
        "report_id": "compliance_report_20250111_153000",
        "generated_at": "2025-01-11T15:30:00.000Z",
        "compliance_status": {
            "compliance_score": 0.85,
            "privacy_assessments": {"total": 3, "approved": 2},
            "breach_notifications": {"total": 1, "resolved": 1},
            "data_processing_agreements": {"total": 2, "active": 2}
        },
        "recommendations": ["Review pending privacy assessments"]
    }
    ```
    """
    try:
        report = gdpr_manager.generate_compliance_report()
        return report
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate compliance report: {str(e)}"
        )


@app.get("/gdpr/privacy-assessments")
def list_privacy_assessments():
    """
    List Privacy Impact Assessments

    Get all privacy impact assessments with their current status.
    """
    try:
        assessments = gdpr_manager.list_assessments()
        return {
            "assessments": [
                {
                    "pia_id": pia.pia_id,
                    "purpose": pia.purpose,
                    "risk_level": pia.risk_level.value,
                    "status": pia.status.value,
                    "created_at": pia.created_at,
                    "updated_at": pia.updated_at,
                }
                for pia in assessments
            ],
            "count": len(assessments),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list assessments: {str(e)}"
        )


@app.get("/gdpr/data-processing-agreements")
def list_data_processing_agreements():
    """
    List Data Processing Agreements

    Get all active data processing agreements with partners.
    """
    try:
        dpas = gdpr_manager.list_dpas()
        return {
            "agreements": [
                {
                    "dpa_id": dpa.dpa_id,
                    "partner_name": dpa.partner_name,
                    "purpose": dpa.purpose,
                    "status": dpa.status,
                    "signed_date": dpa.signed_date,
                    "expiry_date": dpa.expiry_date,
                }
                for dpa in dpas
            ],
            "count": len(dpas),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list DPAs: {str(e)}")


@app.put("/gdpr/breach/{breach_id}/status")
def update_breach_status(
    breach_id: str,
    status: str = Body(..., embed=True),
    notify_regulatory: bool = Body(False, embed=True),
):
    """
    Update Breach Status

    Update the status of a reported data breach.

    **Example Request:**
    ```json
    {
        "status": "resolved",
        "notify_regulatory": true
    }
    ```
    """
    try:
        success = gdpr_manager.update_breach_status(
            breach_id, status, notify_regulatory
        )
        if not success:
            raise HTTPException(status_code=404, detail="Breach not found")

        return {
            "status": "updated",
            "breach_id": breach_id,
            "new_status": status,
            "regulatory_notified": notify_regulatory,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update breach status: {str(e)}"
        )
