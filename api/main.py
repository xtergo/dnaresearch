from datetime import datetime

from access_control import AccessAction, AccessControlManager, AccessRequest
from access_middleware import AccessControlMiddleware
from cache_manager import CacheManager
from collaboration_manager import CollaborationManager, ReactionType
from consent_manager import ConsentManager
from fastapi import Body, FastAPI, HTTPException, Request
from gene_search import GeneSearchEngine
from models import HealthResponse
from security_api import router as security_router

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
    # Basic validation
    required_fields = ["id", "version", "scope", "criteria", "evidence_model"]
    for field in required_fields:
        if field not in theory:
            raise HTTPException(
                status_code=400, detail=f"Missing required field: {field}"
            )

    # Return success response
    return {
        "status": "created",
        "theory_id": theory["id"],
        "version": theory["version"],
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
