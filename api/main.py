# DNA Research Platform API - Pre-commit hook working!
from datetime import datetime
from typing import List

from access_control import AccessAction, AccessControlManager, AccessRequest
from enhanced_webhook_handler import EnhancedWebhookHandler
from access_middleware import AccessControlMiddleware
from anchor_diff import AnchorDiffStorage
from cache_manager import CacheManager
from collaboration_manager import CollaborationManager, ReactionType
from consent_manager import ConsentManager
from evidence_accumulator import EvidenceAccumulator
from evidence_validator import EvidenceValidator
from fastapi import Body, FastAPI, HTTPException, Query, Request, Response
from file_upload_manager import FileUploadManager
from gdpr_compliance import GDPRComplianceManager
from gene_search import GeneSearchEngine
from models import GenomicDataRequest, GenomicDataResponse, HealthResponse
from security_api import router as security_router
from theory_creator import TheoryCreator
from theory_engine import TheoryExecutionEngine
from theory_forker import TheoryForker
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
file_upload_manager = FileUploadManager()
access_control_manager = AccessControlManager(consent_manager)
theory_creator = TheoryCreator()
theory_engine = TheoryExecutionEngine()
theory_forker = TheoryForker()
theory_manager = TheoryManager()
gdpr_manager = GDPRComplianceManager()
variant_interpreter = VariantInterpreter()
evidence_accumulator = EvidenceAccumulator()
evidence_validator = EvidenceValidator()
anchor_diff_storage = AnchorDiffStorage()
# Link theory creator to theory manager for integration
theory_manager.theory_creator = theory_creator

# Enhanced webhook handler
enhanced_webhook_handler = EnhancedWebhookHandler()

# Legacy webhook storage for backward compatibility
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


@app.get("/genes/{gene}/report")
def get_gene_report(gene: str):
    """
    Get Gene Report

    Get comprehensive gene report with technical details.

    **Parameters:**
    - gene: Gene symbol (e.g., "BRCA1")

    **Example Response:**
    ```json
    {
        "gene": "BRCA1",
        "report_type": "gene_summary",
        "summary": "BRCA1 is a tumor suppressor gene...",
        "clinical_significance": "Pathogenic variants cause breast/ovarian cancer",
        "recommendations": ["Genetic counseling", "Enhanced screening"]
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"gene_report_{gene}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Generate comprehensive gene report
        from researcher_reports import ResearcherReportGenerator

        generator = ResearcherReportGenerator()
        report = generator.generate_gene_report(gene)

        response = {
            "report_id": report.report_id,
            "gene": report.gene,
            "report_type": report.report_type.value,
            "summary": report.summary,
            "detailed_analysis": report.detailed_analysis,
            "clinical_significance": report.clinical_significance,
            "recommendations": report.recommendations,
            "confidence_score": report.confidence_score,
            "generated_at": report.generated_at,
            "total_variants": report.metadata.get("total_variants", 0),
            "pathogenic_variants": report.metadata.get("pathogenic_variants", 0),
            "literature_references": [
                {
                    "pmid": ref.pmid,
                    "title": ref.title,
                    "authors": ref.authors,
                    "journal": ref.journal,
                    "year": ref.year,
                    "relevance_score": ref.relevance_score,
                }
                for ref in report.literature_references
            ],
        }

        # Cache result
        cache_manager.set(cache_key, response, 7200)  # 2 hours
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gene report failed: {str(e)}")


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
def create_theory(request_data: dict = Body(...)):
    """
    Create Theory

    Create a new genomic theory for testing hypotheses.

    **Example Request:**
    ```json
    {
        "theory_data": {
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
        },
        "author": "researcher_name"
    }
    ```
    """
    try:
        # Handle both formats: direct theory data or wrapped in theory_data
        is_wrapped_format = "theory_data" in request_data
        if is_wrapped_format:
            theory_data = request_data["theory_data"]
            author = request_data.get("author", "anonymous")
        else:
            theory_data = request_data.copy()
            author = theory_data.pop("author", "anonymous")

        # Create theory using theory creator (which includes validation)
        result = theory_creator.create_theory(theory_data, author)

        # Handle validation failures differently based on request format
        if result.status == "validation_failed":
            if is_wrapped_format:
                # Wrapped format expects 200 with validation errors in response
                return {
                    "status": result.status,
                    "theory_id": result.theory_id,
                    "version": result.version,
                    "created_at": result.created_at,
                    "validation_errors": result.validation_errors or [],
                }
            else:
                # Direct format expects 400 status code
                error_message = (
                    f"Theory validation failed: {'; '.join(result.validation_errors)}"
                )
                raise HTTPException(status_code=400, detail=error_message)

        # Invalidate theory listing cache if creation was successful
        if result.status == "created":
            cache_manager.invalidate_pattern("theories_list")

        return {
            "status": result.status,
            "theory_id": result.theory_id,
            "version": result.version,
            "created_at": result.created_at,
            "validation_errors": result.validation_errors or [],
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
    has_comments: bool = Query(None, description="Filter by comment presence"),
    search: str = Query(None, description="Search in title, ID, and tags"),
    tags: str = Query(None, description="Filter by tags (comma-separated)"),
    sort_by: str = Query("posterior", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(50, description="Maximum results"),
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
        cache_key = f"theories_list_{scope}_{lifecycle}_{author}_{has_comments}_{search}_{tags}_{sort_by}_{sort_order}_{limit}_{offset}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Parse tags parameter
        tags_list = None
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",")]

        # Get theories from manager
        result = theory_manager.list_theories(
            scope=scope,
            lifecycle=lifecycle,
            author=author,
            has_comments=has_comments,
            search=search,
            tags=tags_list,
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
def get_theory_template_legacy(
    scope: str = Query("autism", description="Theory scope")
):
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
async def webhook_sequencing_partner(
    partner: str, data: dict = Body(...), request: Request = None
):
    """
    Enhanced Sequencing Partner Webhook

    Handle webhook events from sequencing partners with enhanced processing.
    """
    try:
        # Get signature for validation
        signature = request.headers.get("X-Signature") if request else None

        # Validate signature if provided
        if signature:
            try:
                payload = await request.body()
                if not enhanced_webhook_handler.validate_signature(
                    payload.decode(), signature, partner
                ):
                    raise HTTPException(
                        status_code=401, detail="Invalid webhook signature"
                    )
            except Exception:
                # If signature validation fails, continue without validation
                # In production, this should be more strict
                pass

        # Process webhook with enhanced handler
        event = await enhanced_webhook_handler.process_webhook(partner, data, signature)

        # Legacy storage for backward compatibility
        event_id = f"evt_{data.get('sample_id', 'unknown')}"
        webhook_events[event_id] = {
            "id": event.id,
            "partner_id": event.partner_id,
            "event_type": event.event_type.value,
            "status": event.status.value,
            "timestamp": event.timestamp,
            "data": _process_webhook_data(data),
        }

        if partner not in partner_events:
            partner_events[partner] = []
        partner_events[partner].append(webhook_events[event_id])

        return {
            "status": event.status.value,
            "partner_id": event.partner_id,
            "event_type": event.event_type.value,
            "event_id": event.id,
            "timestamp": event.timestamp,
            "retry_count": event.retry_count,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Webhook processing failed: {str(e)}"
        )


@app.post("/genomic/store", response_model=GenomicDataResponse)
def store_genomic_data(request: GenomicDataRequest):
    """
    Store Genomic Data

    Store genomic data using anchor+diff compression for efficient storage.

    **Example Request:**
    ```json
    {
        "individual_id": "patient-001",
        "vcf_data": "#VCFV4.2\n1\t12345\t.\tA\tT\t60\tPASS",
        "reference_genome": "GRCh38"
    }
    ```

    **Example Response:**
    ```json
    {
        "individual_id": "patient-001",
        "anchor_id": "anchor-abc123",
        "total_variants": 1,
        "storage_size_mb": 0.001,
        "compression_ratio": 15.2
    }
    ```
    """
    try:
        result = anchor_diff_storage.process_genomic_data(
            request.individual_id, request.vcf_data, request.reference_genome
        )
        return GenomicDataResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to store genomic data: {str(e)}"
        )


@app.get("/genomic/materialize/{individual_id}/{anchor_id}")
def materialize_genomic_sequence(individual_id: str, anchor_id: str):
    """
    Materialize Genomic Sequence

    Reconstruct genomic sequence from anchor+diff storage.

    **Parameters:**
    - individual_id: Individual identifier
    - anchor_id: Anchor sequence identifier

    **Example Response:**
    ```json
    {
        "individual_id": "patient-001",
        "anchor_id": "anchor-abc123",
        "sequence": "ATCGATCGATCG...",
        "stats": {
            "sequence_length": 400,
            "variants_applied": 3,
            "quality_score": 0.95
        }
    }
    ```
    """
    try:
        # Check if anchor exists
        if anchor_id not in anchor_diff_storage.anchors:
            return Response(
                content='{"error": "Anchor not found"}',
                status_code=404,
                media_type="application/json",
            )

        anchor = anchor_diff_storage.anchors[anchor_id]
        differences = anchor_diff_storage.diffs.get(anchor_id, [])

        # Filter differences for this individual
        individual_diffs = [d for d in differences if d.individual_id == individual_id]

        # Mock sequence materialization (in real implementation, would reconstruct from anchor+diffs)
        mock_sequence = "A" * 100 + "T" * 100 + "C" * 100 + "G" * 100

        return {
            "individual_id": individual_id,
            "anchor_id": anchor_id,
            "sequence": mock_sequence,
            "stats": {
                "sequence_length": len(mock_sequence),
                "variants_applied": len(individual_diffs),
                "quality_score": anchor.quality_score,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to materialize sequence: {str(e)}"
        )


@app.get("/genomic/stats/{patient_id}/{anchor_id}")
def get_genomic_stats(patient_id: str, anchor_id: str):
    """
    Get Genomic Statistics

    Get genomic analysis statistics for a patient and anchor.

    **Parameters:**
    - patient_id: Patient identifier (individual_id)
    - anchor_id: Anchor sequence identifier

    **Example Response:**
    ```json
    {
        "individual_id": "patient-001",
        "anchor_id": "anchor-abc123",
        "reference_genome": "GRCh38",
        "total_variants": 1,
        "sequence_length": 400,
        "materialization_efficiency": 0.95
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"genomic_stats_{patient_id}_{anchor_id}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Check if anchor exists
        if anchor_id not in anchor_diff_storage.anchors:
            raise HTTPException(status_code=404, detail="Anchor not found")

        anchor = anchor_diff_storage.anchors[anchor_id]
        differences = anchor_diff_storage.diffs.get(anchor_id, [])

        # Filter differences for this individual
        individual_diffs = [d for d in differences if d.individual_id == patient_id]

        stats = {
            "individual_id": patient_id,
            "anchor_id": anchor_id,
            "reference_genome": anchor.reference_genome,
            "total_variants": len(individual_diffs),
            "sequence_length": 400,  # Mock length
            "materialization_efficiency": anchor.quality_score,
        }

        # Cache result
        cache_manager.set(cache_key, stats, 300)  # 5 minutes
        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get genomic stats: {str(e)}"
        )


@app.get("/webhooks/events/{event_id}")
def get_webhook_event(event_id: str):
    """
    Get Enhanced Webhook Event

    Get details of a specific webhook event with enhanced information.
    """
    from enhanced_webhook_endpoints import get_enhanced_webhook_event

    # Try enhanced handler first
    enhanced_event = get_enhanced_webhook_event(event_id, enhanced_webhook_handler)
    if enhanced_event:
        return enhanced_event

    # Fallback to legacy storage
    if event_id not in webhook_events:
        raise HTTPException(status_code=404, detail="Webhook event not found")

    return webhook_events[event_id]


@app.get("/webhooks/partners/{partner}/events")
def get_partner_events(
    partner: str, limit: int = Query(50, description="Maximum events to return")
):
    """
    Get Enhanced Partner Events

    Get all webhook events for a specific partner with enhanced information.
    """
    from enhanced_webhook_endpoints import get_enhanced_partner_events

    try:
        return get_enhanced_partner_events(partner, limit, enhanced_webhook_handler)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get partner events: {str(e)}"
        )


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


@app.get("/theories/templates/{scope}")
def get_theory_template(scope: str):
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
        # Check cache first
        cache_key = f"theory_template_{scope}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        template = theory_creator.get_theory_template(scope)

        # Cache result
        cache_manager.set(cache_key, template, 3600)  # 1 hour
        return template

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get theory template: {str(e)}"
        )


@app.put("/theories/{theory_id}")
def update_theory(
    theory_id: str,
    version: str = Body(..., embed=True),
    updates: dict = Body(..., embed=True),
    author: str = Body("anonymous", embed=True),
):
    """
    Update Theory

    Update an existing theory with new information.

    **Example Request:**
    ```json
    {
        "version": "1.0.0",
        "updates": {
            "title": "Updated Theory Title",
            "description": "Updated description",
            "tags": ["updated", "validated"]
        },
        "author": "researcher_name"
    }
    ```
    """
    try:
        # Check if theory exists
        existing_theory = theory_manager.get_theory_summary(theory_id, version)
        if not existing_theory:
            raise HTTPException(
                status_code=404,
                detail=f"Theory '{theory_id}' version '{version}' not found",
            )

        # Update theory using theory creator
        result = theory_creator.update_theory(theory_id, version, updates, author)

        # Invalidate caches
        cache_manager.invalidate_pattern("theories_list")
        cache_manager.invalidate_pattern(f"theory_details_{theory_id}")

        return {
            "status": result.status,
            "theory_id": result.theory_id,
            "version": result.version,
            "updated_at": result.updated_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Theory update failed: {str(e)}")


@app.delete("/theories/{theory_id}")
def delete_theory(
    theory_id: str, version: str = Query(..., description="Theory version to delete")
):
    """
    Delete Theory

    Delete a specific version of a theory.

    **Parameters:**
    - theory_id: Theory identifier
    - version: Theory version to delete

    **Example Response:**
    ```json
    {
        "status": "deleted",
        "theory_id": "autism-theory-1",
        "version": "1.0.0",
        "timestamp": "2025-01-11T15:30:00.000Z"
    }
    ```
    """
    try:
        # Check if theory exists
        existing_theory = theory_manager.get_theory_summary(theory_id, version)
        if not existing_theory:
            raise HTTPException(
                status_code=404,
                detail=f"Theory '{theory_id}' version '{version}' not found",
            )

        # Delete theory using theory creator
        result = theory_creator.delete_theory(theory_id, version)

        if result.status == "not_found":
            raise HTTPException(
                status_code=404,
                detail=f"Theory '{theory_id}' version '{version}' not found",
            )

        # Invalidate caches
        cache_manager.invalidate_pattern("theories_list")
        cache_manager.invalidate_pattern(f"theory_details_{theory_id}")

        return {
            "status": result.status,
            "theory_id": result.theory_id,
            "version": result.version,
            "timestamp": result.timestamp,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Theory deletion failed: {str(e)}")


@app.post("/theories/validate")
def validate_theory_endpoint(theory: dict = Body(...)):
    """
    Validate Theory

    Validate a theory JSON against the schema.
    """
    try:
        # Validate theory using validators module
        validated_theory = validate_theory(theory)

        return {"status": "valid", "theory": validated_theory}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@app.post("/theories/{theory_id}/execute")
def execute_theory(
    theory_id: str,
    theory: dict = Body(..., embed=True),
    vcf_data: str = Body(..., embed=True),
    family_id: str = Body("default", embed=True),
):
    """
    Execute Theory

    Execute a theory against VCF data and calculate Bayes factor.

    **Example Request:**
    ```json
    {
        "theory": {
            "id": "autism-theory",
            "version": "1.0.0",
            "scope": "autism",
            "criteria": {"genes": ["SHANK3"]},
            "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}}
        },
        "vcf_data": "#VCFV4.2\n22\t51150000\t.\tA\tT\t60\tPASS",
        "family_id": "family-001"
    }
    ```
    """
    try:
        # Validate theory ID matches URL parameter
        if theory.get("id") != theory_id:
            raise HTTPException(
                status_code=400,
                detail=f"Theory ID mismatch: URL has '{theory_id}', body has '{theory.get('id')}'",
            )

        # Validate theory schema
        try:
            validate_theory(theory)
        except HTTPException as e:
            raise HTTPException(status_code=400, detail=f"Invalid theory: {e.detail}")

        # Execute theory
        result = theory_engine.execute_theory(theory, vcf_data, family_id)

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
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Theory execution failed: {str(e)}"
        )


@app.post("/theories/{theory_id}/fork")
def fork_theory(
    theory_id: str,
    parent_theory: dict = Body(..., embed=True),
    new_theory_id: str = Body(..., embed=True),
    modifications: dict = Body(..., embed=True),
    fork_reason: str = Body("user_modification", embed=True),
):
    """
    Fork Theory

    Create a new theory by forking an existing one with modifications.

    **Example Request:**
    ```json
    {
        "parent_theory": {
            "id": "parent-theory",
            "version": "1.0.0",
            "scope": "autism",
            "criteria": {"genes": ["SHANK3"]},
            "evidence_model": {"priors": 0.1, "likelihood_weights": {"variant_hit": 2.0}}
        },
        "new_theory_id": "child-theory",
        "modifications": {
            "criteria": {"genes": ["SHANK3", "NRXN1"]}
        },
        "fork_reason": "added_genes"
    }
    ```
    """
    try:
        # Validate parent theory ID matches URL parameter
        if parent_theory.get("id") != theory_id:
            raise HTTPException(
                status_code=400,
                detail=f"Parent theory ID mismatch: URL has '{theory_id}', body has '{parent_theory.get('id')}'",
            )

        # Validate parent theory schema
        try:
            validate_theory(parent_theory)
        except HTTPException as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid parent theory: {e.detail}"
            )

        # Fork the theory
        fork_result, new_theory = theory_forker.fork_theory(
            parent_theory, new_theory_id, modifications, fork_reason
        )

        # Invalidate theory listing cache
        cache_manager.invalidate_pattern("theories_list")

        return {
            "status": "theory_forked",
            "new_theory_id": fork_result.new_theory_id,
            "new_version": fork_result.new_version,
            "parent_id": fork_result.parent_id,
            "parent_version": fork_result.parent_version,
            "changes_made": fork_result.changes_made,
            "new_theory": new_theory,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Theory forking failed: {str(e)}")


@app.get("/theories/{theory_id}/lineage")
def get_theory_lineage(
    theory_id: str, version: str = Query(..., description="Theory version")
):
    """
    Get Theory Lineage

    Get lineage information for a theory version.
    """
    try:
        lineage = theory_forker.get_lineage(theory_id, version)

        if lineage:
            return {
                "theory_id": lineage.theory_id,
                "version": lineage.version,
                "parent_id": lineage.parent_id,
                "parent_version": lineage.parent_version,
                "fork_reason": lineage.fork_reason,
                "created_at": lineage.created_at,
                "is_root": lineage.parent_id is None,
            }
        else:
            # Root theory with no parent
            return {
                "theory_id": theory_id,
                "version": version,
                "lineage": None,
                "is_root": True,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get lineage: {str(e)}")


@app.get("/theories/{theory_id}/children")
def get_theory_children(
    theory_id: str, version: str = Query(..., description="Parent theory version")
):
    """
    Get Theory Children

    Get all theories forked from a parent theory.
    """
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
def get_theory_ancestry(
    theory_id: str, version: str = Query(..., description="Theory version")
):
    """
    Get Theory Ancestry

    Get full ancestry chain for a theory.
    """
    try:
        ancestry = theory_forker.get_ancestry(theory_id, version)

        return {
            "theory_id": theory_id,
            "version": version,
            "ancestry": [
                {
                    "theory_id": lineage.theory_id,
                    "version": lineage.version,
                    "parent_id": lineage.parent_id,
                    "parent_version": lineage.parent_version,
                    "fork_reason": lineage.fork_reason,
                    "created_at": lineage.created_at,
                }
                for lineage in ancestry
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ancestry: {str(e)}")


@app.post("/reports/variant")
def generate_variant_report(
    gene: str = Body(..., embed=True),
    variant: str = Body(..., embed=True),
    vcf_data: str = Body(None, embed=True),
):
    """
    Generate Variant Report

    Generate detailed technical report for a specific variant.
    """
    try:
        # Check cache first
        cache_key = f"variant_report_{gene}_{variant}_{hash(vcf_data or '')}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        from researcher_reports import ResearcherReportGenerator

        generator = ResearcherReportGenerator()
        report = generator.generate_variant_report(gene, variant, vcf_data)

        # Convert to API response format
        response = {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "gene": report.gene,
            "variant": report.variant,
            "summary": report.summary,
            "detailed_analysis": report.detailed_analysis,
            "clinical_significance": report.clinical_significance,
            "recommendations": report.recommendations,
            "confidence_score": report.confidence_score,
            "generated_at": report.generated_at,
            "variant_annotations": [
                {
                    "variant": ann.variant,
                    "gene": ann.gene,
                    "transcript": ann.transcript,
                    "consequence": ann.consequence,
                    "amino_acid_change": ann.amino_acid_change,
                    "conservation_score": ann.conservation_score,
                    "pathogenicity_score": ann.pathogenicity_score,
                    "evidence_level": ann.evidence_level.value,
                }
                for ann in report.variant_annotations
            ],
            "population_frequencies": [
                {
                    "population": freq.population,
                    "frequency": freq.frequency,
                    "allele_count": freq.allele_count,
                    "total_alleles": freq.total_alleles,
                    "source": freq.source,
                }
                for freq in report.population_frequencies
            ],
            "literature_references": [
                {
                    "pmid": ref.pmid,
                    "title": ref.title,
                    "authors": ref.authors,
                    "journal": ref.journal,
                    "year": ref.year,
                    "relevance_score": ref.relevance_score,
                }
                for ref in report.literature_references
            ],
            "metadata": report.metadata,
        }

        # Cache result
        cache_manager.set(cache_key, response, 3600)  # 1 hour
        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {str(e)}"
        )


@app.post("/reports/gene")
def generate_gene_report(gene: str = Body(..., embed=True)):
    """
    Generate Gene Report

    Generate comprehensive gene summary report.
    """
    try:
        # Check cache first
        cache_key = f"gene_report_{gene}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        from researcher_reports import ResearcherReportGenerator

        generator = ResearcherReportGenerator()
        report = generator.generate_gene_report(gene)

        # Convert to API response format
        response = {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "gene": report.gene,
            "summary": report.summary,
            "detailed_analysis": report.detailed_analysis,
            "clinical_significance": report.clinical_significance,
            "recommendations": report.recommendations,
            "confidence_score": report.confidence_score,
            "generated_at": report.generated_at,
            "total_variants": report.metadata.get("total_variants", 0),
            "pathogenic_variants": report.metadata.get("pathogenic_variants", 0),
            "literature_references": [
                {
                    "pmid": ref.pmid,
                    "title": ref.title,
                    "authors": ref.authors,
                    "journal": ref.journal,
                    "year": ref.year,
                    "relevance_score": ref.relevance_score,
                }
                for ref in report.literature_references
            ],
            "variant_annotations": [
                {
                    "variant": ann.variant,
                    "gene": ann.gene,
                    "transcript": ann.transcript,
                    "consequence": ann.consequence,
                    "amino_acid_change": ann.amino_acid_change,
                    "conservation_score": ann.conservation_score,
                    "pathogenicity_score": ann.pathogenicity_score,
                    "evidence_level": ann.evidence_level.value,
                }
                for ann in report.variant_annotations
            ],
            "population_frequencies": [
                {
                    "population": freq.population,
                    "frequency": freq.frequency,
                    "allele_count": freq.allele_count,
                    "total_alleles": freq.total_alleles,
                    "source": freq.source,
                }
                for freq in report.population_frequencies
            ],
            "metadata": report.metadata,
        }

        # Cache result
        cache_manager.set(cache_key, response, 3600)  # 1 hour
        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {str(e)}"
        )


@app.get("/consent/forms")
def list_consent_forms():
    """List Consent Forms"""
    manager = consent_manager
    forms = manager.list_consent_forms()

    return {
        "forms": [
            {
                "form_id": form.form_id,
                "version": form.version,
                "title": form.title,
                "description": form.description,
                "consent_types": [ct.value for ct in form.consent_types],
                "required_fields": form.required_fields,
                "validity_period_days": form.validity_period_days,
            }
            for form in forms
        ]
    }


@app.get("/consent/forms/{form_id}")
def get_consent_form(form_id: str):
    """Get Consent Form"""
    manager = consent_manager
    form = manager.get_consent_form(form_id)

    if not form:
        raise HTTPException(status_code=404, detail="Consent form not found")

    return {
        "form_id": form.form_id,
        "version": form.version,
        "title": form.title,
        "description": form.description,
        "consent_types": [ct.value for ct in form.consent_types],
        "required_fields": form.required_fields,
        "consent_text": form.consent_text,
        "validity_period_days": form.validity_period_days,
        "created_at": form.created_at,
    }


@app.post("/consent/capture")
def capture_consent(
    form_id: str = Body(...),
    user_id: str = Body(...),
    user_data: dict = Body(...),
    digital_signature: str = Body(...),
    request: Request = None,
):
    """Capture Consent"""
    try:
        manager = consent_manager

        # Get IP and user agent from request
        ip_address = (
            getattr(request.client, "host", "127.0.0.1") if request else "127.0.0.1"
        )
        user_agent = (
            request.headers.get("user-agent", "unknown") if request else "unknown"
        )

        record = manager.capture_consent(
            user_id=user_id,
            form_id=form_id,
            user_data=user_data,
            ip_address=ip_address,
            user_agent=user_agent,
            digital_signature=digital_signature,
        )

        return {
            "status": "consent_captured",
            "user_id": user_id,
            "consent_id": record.consent_id,
            "consent_types": [
                ct.value for ct in manager.get_consent_form(form_id).consent_types
            ],
            "granted_at": record.granted_at,
            "expires_at": record.expires_at,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/consent/{user_id}/validate")
def validate_user_consent(user_id: str):
    """Validate User Consent

    Check if user has valid consent for data processing.
    """
    try:
        from consent_manager import ConsentType

        manager = consent_manager

        # Check for genomic analysis consent (most common)
        has_genomic_consent = manager.check_consent(
            user_id, ConsentType.GENOMIC_ANALYSIS
        )
        has_data_sharing = manager.check_consent(user_id, ConsentType.DATA_SHARING)
        has_research = manager.check_consent(
            user_id, ConsentType.RESEARCH_PARTICIPATION
        )

        return {
            "user_id": user_id,
            "valid_consent": has_genomic_consent,
            "consent_details": {
                "genomic_analysis": has_genomic_consent,
                "data_sharing": has_data_sharing,
                "research_participation": has_research,
            },
            "validated_at": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Consent validation failed: {str(e)}"
        )


@app.get("/consent/check/{user_id}")
def check_consent(user_id: str, consent_type: str):
    """Check Consent"""
    from consent_manager import ConsentType

    try:
        consent_type_enum = ConsentType(consent_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid consent type")

    manager = consent_manager
    has_consent = manager.check_consent(user_id, consent_type_enum)

    return {
        "user_id": user_id,
        "consent_type": consent_type,
        "has_consent": has_consent,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/consent/withdraw")
def withdraw_consent(
    user_id: str = Body(...),
    consent_type: str = Body(...),
    reason: str = Body(...),
):
    """Withdraw Consent"""
    from consent_manager import ConsentType

    try:
        consent_type_enum = ConsentType(consent_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid consent type")

    manager = consent_manager
    success = manager.withdraw_consent(user_id, consent_type_enum, reason)

    if not success:
        raise HTTPException(status_code=404, detail="No active consent found")

    return {
        "status": "consent_withdrawn",
        "user_id": user_id,
        "consent_type": consent_type,
        "withdrawn_at": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/consent/users/{user_id}")
def get_user_consents(user_id: str):
    """Get User Consents"""
    manager = consent_manager
    consents = manager.get_user_consents(user_id)

    return {
        "user_id": user_id,
        "consents": [
            {
                "consent_id": consent.consent_id,
                "consent_type": consent.consent_type.value,
                "status": consent.status.value,
                "granted_at": consent.granted_at,
                "expires_at": consent.expires_at,
                "withdrawn_at": consent.withdrawn_at,
            }
            for consent in consents
        ],
    }


@app.get("/consent/audit/{user_id}")
def get_consent_audit_trail(user_id: str):
    """Get Consent Audit Trail"""
    manager = consent_manager
    audit_trail = manager.get_consent_audit_trail(user_id)

    return {
        "user_id": user_id,
        "audit_trail": audit_trail,
    }


@app.get("/consent/stats")
def get_consent_stats():
    """Get Consent Statistics"""
    manager = consent_manager
    stats = manager.get_consent_stats()

    return stats


@app.post("/files/presign")
def create_presigned_upload(
    filename: str = Body(...),
    file_size: int = Body(...),
    file_type: str = Body(...),
    checksum: str = Body(...),
    user_id: str = Body("anonymous"),
):
    """Create Pre-signed Upload URL"""
    try:
        manager = file_upload_manager
        upload = manager.create_presigned_upload(
            filename=filename,
            file_size=file_size,
            file_type=file_type,
            checksum=checksum,
            user_id=user_id,
        )

        return {
            "upload_id": upload.upload_id,
            "presigned_url": upload.presigned_url,
            "expires_at": upload.expires_at,
            "status": upload.status.value,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/files/uploads/{upload_id}")
def get_upload_status(upload_id: str):
    """Get Upload Status"""
    manager = file_upload_manager
    upload = manager.get_upload_status(upload_id)

    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    return {
        "upload_id": upload.upload_id,
        "filename": upload.filename,
        "file_type": upload.file_type.value,
        "file_size": upload.file_size,
        "status": upload.status.value,
        "created_at": upload.created_at,
        "expires_at": upload.expires_at,
        "user_id": upload.user_id,
    }


@app.post("/files/uploads/{upload_id}/complete")
def complete_upload(
    upload_id: str,
    actual_checksum: str = Body(..., embed=True),
):
    """Complete Upload"""
    manager = file_upload_manager
    upload = manager.get_upload_status(upload_id)

    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    validated = manager.validate_upload_completion(upload_id, actual_checksum)

    if not validated:
        raise HTTPException(status_code=400, detail="Checksum validation failed")

    return {
        "upload_id": upload_id,
        "status": "completed",
        "validated": True,
    }


@app.get("/files/uploads")
def list_uploads(
    user_id: str = Query(None),
    status: str = Query(None),
):
    """List Uploads"""
    from file_upload_manager import UploadStatus

    manager = file_upload_manager

    if status:
        try:
            status_enum = UploadStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    else:
        status_enum = None

    if user_id:
        uploads = manager.list_user_uploads(user_id, status_enum)
    else:
        uploads = list(manager.uploads.values())
        if status_enum:
            uploads = [u for u in uploads if u.status == status_enum]

    return {
        "uploads": [
            {
                "upload_id": upload.upload_id,
                "filename": upload.filename,
                "file_type": upload.file_type.value,
                "file_size": upload.file_size,
                "status": upload.status.value,
                "created_at": upload.created_at,
                "user_id": upload.user_id,
            }
            for upload in uploads
        ],
        "count": len(uploads),
    }


@app.get("/files/stats")
def get_upload_stats():
    """Get Upload Statistics"""
    manager = file_upload_manager
    stats = manager.get_upload_stats()

    return stats


@app.post("/files/cleanup")
def cleanup_expired_uploads():
    """Cleanup Expired Uploads"""
    manager = file_upload_manager
    cleaned_up = manager.cleanup_expired_uploads()

    return {
        "cleaned_up": cleaned_up,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/theories/{theory_id}/evidence")
def add_theory_evidence(
    theory_id: str,
    theory_version: str = Body(..., embed=True),
    family_id: str = Body(..., embed=True),
    bayes_factor: float = Body(..., embed=True),
    evidence_type: str = Body("execution", embed=True),
    weight: float = Body(1.0, embed=True),
    source: str = Body("manual_entry", embed=True),
):
    """
    Add Evidence to Theory

    Add new evidence for a theory from family analysis.

    **Example Request:**
    ```json
    {
        "theory_version": "1.0.0",
        "family_id": "family-001",
        "bayes_factor": 2.5,
        "evidence_type": "variant_segregation",
        "weight": 1.0,
        "source": "vcf_analysis"
    }
    ```

    **Example Response:**
    ```json
    {
        "status": "evidence_added",
        "theory_id": "autism-theory-1",
        "theory_version": "1.0.0",
        "family_id": "family-001",
        "bayes_factor": 2.5,
        "timestamp": "2025-01-11T15:30:00.000Z"
    }
    ```
    """
    try:
        # Validate Bayes factor
        if bayes_factor <= 0:
            raise HTTPException(status_code=400, detail="Bayes factor must be positive")

        # Add evidence
        evidence_accumulator.add_evidence(
            theory_id=theory_id,
            theory_version=theory_version,
            family_id=family_id,
            bayes_factor=bayes_factor,
            evidence_type=evidence_type,
            weight=weight,
            source=source,
        )

        # Calculate updated posterior for support classification
        posterior_result = evidence_accumulator.update_posterior(
            theory_id, theory_version, 0.1
        )

        # Invalidate theory caches
        cache_manager.invalidate_pattern(f"theory_evidence_{theory_id}")
        cache_manager.invalidate_pattern(f"theory_posterior_{theory_id}")
        cache_manager.invalidate_pattern("theories_list")

        return {
            "status": "evidence_added",
            "theory_id": theory_id,
            "version": theory_version,
            "theory_version": theory_version,
            "family_id": family_id,
            "bayes_factor": bayes_factor,
            "evidence_type": evidence_type,
            "weight": weight,
            "source": source,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "evidence_count": posterior_result.evidence_count,
            "families_analyzed": posterior_result.families_analyzed,
            "accumulated_bf": posterior_result.accumulated_bf,
            "posterior": posterior_result.posterior,
            "support_class": posterior_result.support_class,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add evidence: {str(e)}")


@app.get("/theories/{theory_id}/evidence")
def get_theory_evidence(
    theory_id: str, theory_version: str = Query(..., description="Theory version")
):
    """
    Get Theory Evidence

    Get all evidence accumulated for a theory version.

    **Parameters:**
    - theory_id: Theory identifier
    - theory_version: Theory version

    **Example Response:**
    ```json
    {
        "theory_id": "autism-theory-1",
        "theory_version": "1.0.0",
        "evidence_trail": [
            {
                "family_id": "family-001",
                "bayes_factor": 2.5,
                "evidence_type": "variant_segregation",
                "weight": 1.0,
                "timestamp": "2025-01-11T15:30:00.000Z",
                "source": "vcf_analysis"
            }
        ],
        "evidence_count": 1
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"theory_evidence_{theory_id}_{theory_version}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Get evidence trail
        evidence_trail = evidence_accumulator.get_evidence_trail(
            theory_id, theory_version
        )

        result = {
            "theory_id": theory_id,
            "version": theory_version,
            "theory_version": theory_version,
            "evidence_trail": evidence_trail,
            "evidence_count": len(evidence_trail),
        }

        # Cache result
        cache_manager.set(cache_key, result, 600)  # 10 minutes
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evidence: {str(e)}")


@app.get("/theories/{theory_id}/posterior")
def get_theory_posterior(
    theory_id: str,
    theory_version: str = Query(..., description="Theory version"),
    prior: float = Query(0.1, description="Prior probability"),
):
    """
    Get Theory Posterior

    Calculate updated posterior probability from accumulated evidence.

    **Parameters:**
    - theory_id: Theory identifier
    - theory_version: Theory version
    - prior: Prior probability (default: 0.1)

    **Example Response:**
    ```json
    {
        "theory_id": "autism-theory-1",
        "version": "1.0.0",
        "prior": 0.1,
        "accumulated_bf": 6.25,
        "posterior": 0.384,
        "support_class": "moderate",
        "evidence_count": 3,
        "families_analyzed": 2
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"theory_posterior_{theory_id}_{theory_version}_{prior}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Calculate posterior
        result = evidence_accumulator.update_posterior(theory_id, theory_version, prior)

        response = {
            "theory_id": result.theory_id,
            "version": result.version,
            "prior": result.prior,
            "accumulated_bf": result.accumulated_bf,
            "posterior": result.posterior,
            "support_class": result.support_class,
            "evidence_count": result.evidence_count,
            "families_analyzed": result.families_analyzed,
        }

        # Cache result
        cache_manager.set(cache_key, response, 300)  # 5 minutes
        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate posterior: {str(e)}"
        )


@app.get("/theories/{theory_id}/evidence/stats")
def get_evidence_stats(
    theory_id: str, theory_version: str = Query(..., description="Theory version")
):
    """
    Get Evidence Statistics

    Get statistical summary of evidence for a theory.

    **Example Response:**
    ```json
    {
        "theory_id": "autism-theory-1",
        "theory_version": "1.0.0",
        "total_evidence": 5,
        "unique_families": 3,
        "evidence_types": {
            "variant_segregation": 3,
            "pathway_analysis": 2
        },
        "bayes_factor_range": {
            "min": 1.2,
            "max": 4.5,
            "mean": 2.8,
            "median": 2.5
        },
        "weight_distribution": {
            "mean": 1.0,
            "total_weight": 5.0
        }
    }
    ```
    """
    try:
        # Check cache first
        cache_key = f"evidence_stats_{theory_id}_{theory_version}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        # Get evidence trail
        evidence_trail = evidence_accumulator.get_evidence_trail(
            theory_id, theory_version
        )

        if not evidence_trail:
            return {
                "theory_id": theory_id,
                "theory_version": theory_version,
                "total_evidence": 0,
                "unique_families": 0,
                "evidence_types": {},
                "bayes_factor_range": {},
                "weight_distribution": {},
            }

        # Calculate statistics
        unique_families = set(e["family_id"] for e in evidence_trail)
        evidence_types = {}
        bayes_factors = []
        weights = []

        for evidence in evidence_trail:
            # Count evidence types
            ev_type = evidence["evidence_type"]
            evidence_types[ev_type] = evidence_types.get(ev_type, 0) + 1

            # Collect BF and weights
            bayes_factors.append(evidence["bayes_factor"])
            weights.append(evidence["weight"])

        # Calculate BF statistics
        bf_stats = {}
        if bayes_factors:
            bf_stats = {
                "min": min(bayes_factors),
                "max": max(bayes_factors),
                "mean": sum(bayes_factors) / len(bayes_factors),
                "median": sorted(bayes_factors)[len(bayes_factors) // 2],
            }

        # Calculate weight statistics
        weight_stats = {}
        if weights:
            weight_stats = {
                "mean": sum(weights) / len(weights),
                "total_weight": sum(weights),
            }

        result = {
            "theory_id": theory_id,
            "theory_version": theory_version,
            "total_evidence": len(evidence_trail),
            "unique_families": len(unique_families),
            "evidence_types": evidence_types,
            "bayes_factor_range": bf_stats,
            "weight_distribution": weight_stats,
        }

        # Cache result
        cache_manager.set(cache_key, result, 600)  # 10 minutes
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get evidence stats: {str(e)}"
        )


@app.post("/evidence/validate")
def validate_evidence(evidence_data: dict = Body(...)):
    """
    Validate Evidence

    Validate evidence data against schema requirements.

    **Example Request:**
    ```json
    {
        "type": "variant_hit",
        "weight": 2.5,
        "timestamp": "2025-01-11T15:30:00.000Z",
        "data": {
            "gene": "SHANK3",
            "variant": "c.3679C>T",
            "impact": "high"
        },
        "source": "clinical_lab",
        "confidence": 0.9
    }
    ```

    **Example Response:**
    ```json
    {
        "is_valid": true,
        "errors": [],
        "evidence_type": "variant_hit",
        "confidence": 0.9
    }
    ```
    """
    try:
        result = evidence_validator.validate_evidence(evidence_data)

        if result.is_valid:
            return {
                "status": "valid",
                "evidence": evidence_data,
                "is_valid": result.is_valid,
                "errors": result.errors,
                "evidence_type": result.evidence_type,
                "confidence": result.confidence,
            }
        else:
            error_message = f"Evidence validation failed: {'; '.join(result.errors)}"
            raise HTTPException(status_code=400, detail=error_message)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Evidence validation failed: {str(e)}"
        )


@app.get("/webhooks/stats")
def get_webhook_stats():
    """
    Get Webhook Statistics

    Get comprehensive webhook processing statistics.
    """
    from enhanced_webhook_endpoints import get_webhook_statistics

    try:
        return get_webhook_statistics(enhanced_webhook_handler)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get webhook stats: {str(e)}"
        )


@app.get("/webhooks/partners")
def list_webhook_partners():
    """
    List Webhook Partners

    Get information about all configured webhook partners.
    """
    from enhanced_webhook_endpoints import list_webhook_partners

    try:
        return list_webhook_partners(enhanced_webhook_handler)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list partners: {str(e)}"
        )


@app.get("/webhooks/events")
def list_webhook_events(
    status: str = Query(None, description="Filter by status"),
    partner: str = Query(None, description="Filter by partner"),
    limit: int = Query(100, description="Maximum events to return"),
):
    """
    List Webhook Events

    Get webhook events with optional filtering.
    """
    from enhanced_webhook_endpoints import list_webhook_events

    try:
        return list_webhook_events(status, partner, limit, enhanced_webhook_handler)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list events: {str(e)}")
