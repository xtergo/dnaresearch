"""Theory management for listing, filtering, and sorting"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class TheoryScope(Enum):
    AUTISM = "autism"
    CANCER = "cancer"
    CARDIOVASCULAR = "cardiovascular"
    NEUROLOGICAL = "neurological"
    METABOLIC = "metabolic"


class TheoryLifecycle(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class TheoryMetadata:
    id: str
    version: str
    title: str
    scope: str
    lifecycle: str
    author: str
    created_at: str
    updated_at: str
    evidence_count: int
    posterior: float
    support_class: str
    tags: List[str]
    has_comments: bool


class TheoryManager:
    """Manage theory listing, filtering, and sorting"""

    def __init__(self):
        # Mock theory database - in production this would be a real database
        self.theories = self._load_mock_theories()

    def _load_mock_theories(self) -> List[TheoryMetadata]:
        """Load mock theory data"""
        return [
            TheoryMetadata(
                id="autism-theory-1",
                version="1.2.0",
                title="SHANK3 Variants in Autism Spectrum Disorders",
                scope="autism",
                lifecycle="active",
                author="dr.smith",
                created_at="2024-12-15T10:00:00Z",
                updated_at="2025-01-10T14:30:00Z",
                evidence_count=15,
                posterior=0.75,
                support_class="strong",
                tags=["synaptic", "de-novo", "validated"],
                has_comments=True,
            ),
            TheoryMetadata(
                id="autism-theory-2",
                version="2.0.1",
                title="Synaptic Gene Network in ASD",
                scope="autism",
                lifecycle="active",
                author="dr.jones",
                created_at="2024-11-20T09:15:00Z",
                updated_at="2025-01-08T11:20:00Z",
                evidence_count=8,
                posterior=0.62,
                support_class="moderate",
                tags=["network", "pathway", "synaptic"],
                has_comments=False,
            ),
            TheoryMetadata(
                id="cancer-theory-1",
                version="1.0.0",
                title="BRCA1/2 Pathogenic Variants",
                scope="cancer",
                lifecycle="active",
                author="dr.wilson",
                created_at="2024-10-05T16:45:00Z",
                updated_at="2024-12-20T13:10:00Z",
                evidence_count=25,
                posterior=0.89,
                support_class="strong",
                tags=["hereditary", "breast-cancer", "validated"],
                has_comments=True,
            ),
            TheoryMetadata(
                id="neuro-theory-1",
                version="1.1.2",
                title="APOE4 in Alzheimer's Disease Risk",
                scope="neurological",
                lifecycle="active",
                author="dr.brown",
                created_at="2024-09-12T08:30:00Z",
                updated_at="2025-01-05T10:45:00Z",
                evidence_count=32,
                posterior=0.81,
                support_class="strong",
                tags=["alzheimer", "risk-factor", "population"],
                has_comments=True,
            ),
            TheoryMetadata(
                id="autism-theory-3",
                version="0.5.0",
                title="CHD8 Chromatin Remodeling Theory",
                scope="autism",
                lifecycle="draft",
                author="dr.garcia",
                created_at="2025-01-01T12:00:00Z",
                updated_at="2025-01-11T09:15:00Z",
                evidence_count=3,
                posterior=0.45,
                support_class="weak",
                tags=["chromatin", "draft", "early-stage"],
                has_comments=False,
            ),
            TheoryMetadata(
                id="cardio-theory-1",
                version="1.3.1",
                title="Familial Hypercholesterolemia Variants",
                scope="cardiovascular",
                lifecycle="deprecated",
                author="dr.lee",
                created_at="2024-06-10T14:20:00Z",
                updated_at="2024-11-15T16:30:00Z",
                evidence_count=18,
                posterior=0.68,
                support_class="moderate",
                tags=["cholesterol", "familial", "deprecated"],
                has_comments=True,
            ),
        ]

    def list_theories(
        self,
        scope: Optional[str] = None,
        lifecycle: Optional[str] = None,
        author: Optional[str] = None,
        has_comments: Optional[bool] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "posterior",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List theories with filtering and sorting"""

        # Start with all theories
        filtered_theories = self.theories.copy()

        # Add created theories if theory_creator is available
        if hasattr(self, "theory_creator") and self.theory_creator:
            for theory_key, theory_data in self.theory_creator.created_theories.items():
                created_theory = TheoryMetadata(
                    id=theory_data["id"],
                    version=theory_data["version"],
                    title=theory_data.get("title", theory_data["id"]),
                    scope=theory_data["scope"],
                    lifecycle=theory_data.get("lifecycle", "draft"),
                    author=theory_data.get("author", "anonymous"),
                    created_at=theory_data.get("created_at", ""),
                    updated_at=theory_data.get("updated_at", ""),
                    evidence_count=0,
                    posterior=0.5,
                    support_class="weak",
                    tags=theory_data.get("tags", []),
                    has_comments=False,
                )
                filtered_theories.append(created_theory)

        # Apply filters
        if scope:
            filtered_theories = [t for t in filtered_theories if t.scope == scope]

        if lifecycle:
            filtered_theories = [
                t for t in filtered_theories if t.lifecycle == lifecycle
            ]

        if author:
            filtered_theories = [t for t in filtered_theories if t.author == author]

        if has_comments is not None:
            filtered_theories = [
                t for t in filtered_theories if t.has_comments == has_comments
            ]

        if search:
            search_lower = search.lower()
            filtered_theories = [
                t
                for t in filtered_theories
                if (
                    search_lower in t.title.lower()
                    or search_lower in t.id.lower()
                    or any(search_lower in tag.lower() for tag in t.tags)
                )
            ]

        if tags:
            filtered_theories = [
                t for t in filtered_theories if any(tag in t.tags for tag in tags)
            ]

        # Apply sorting
        reverse = sort_order == "desc"

        if sort_by == "posterior":
            filtered_theories.sort(key=lambda t: t.posterior, reverse=reverse)
        elif sort_by == "evidence_count":
            filtered_theories.sort(key=lambda t: t.evidence_count, reverse=reverse)
        elif sort_by == "created_at":
            filtered_theories.sort(key=lambda t: t.created_at, reverse=reverse)
        elif sort_by == "updated_at":
            filtered_theories.sort(key=lambda t: t.updated_at, reverse=reverse)
        elif sort_by == "title":
            filtered_theories.sort(key=lambda t: t.title.lower(), reverse=reverse)

        # Apply pagination
        total_count = len(filtered_theories)
        paginated_theories = filtered_theories[offset : offset + limit]

        return {
            "theories": [self._theory_to_dict(t) for t in paginated_theories],
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count,
        }

    def get_theory_summary(
        self, theory_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get theory summary by ID"""
        # Check created theories first if theory_creator is available
        if hasattr(self, "theory_creator") and self.theory_creator:
            created_theory = self.theory_creator.get_theory(
                theory_id, version or "1.0.0"
            )
            if created_theory:
                return {
                    "id": created_theory["id"],
                    "version": created_theory["version"],
                    "title": created_theory.get("title", created_theory["id"]),
                    "scope": created_theory["scope"],
                    "lifecycle": created_theory.get("lifecycle", "draft"),
                    "author": created_theory.get("author", "anonymous"),
                    "created_at": created_theory.get("created_at", ""),
                    "updated_at": created_theory.get("updated_at", ""),
                    "evidence_count": 0,
                    "posterior": 0.5,
                    "support_class": "weak",
                    "tags": created_theory.get("tags", []),
                    "has_comments": False,
                }

        # Check mock theories
        for theory in self.theories:
            if theory.id == theory_id and (
                version is None or theory.version == version
            ):
                return self._theory_to_dict(theory)
        return None

    def get_theory_stats(self) -> Dict[str, Any]:
        """Get overall theory statistics"""
        all_theories = self.theories.copy()

        # Add created theories if theory_creator is available
        if hasattr(self, "theory_creator") and self.theory_creator:
            for theory_key, theory_data in self.theory_creator.created_theories.items():
                created_theory = TheoryMetadata(
                    id=theory_data["id"],
                    version=theory_data["version"],
                    title=theory_data.get("title", theory_data["id"]),
                    scope=theory_data["scope"],
                    lifecycle=theory_data.get("lifecycle", "draft"),
                    author=theory_data.get("author", "anonymous"),
                    created_at=theory_data.get("created_at", ""),
                    updated_at=theory_data.get("updated_at", ""),
                    evidence_count=0,
                    posterior=0.5,
                    support_class="weak",
                    tags=theory_data.get("tags", []),
                    has_comments=False,
                )
                all_theories.append(created_theory)

        total_theories = len(all_theories)
        active_theories = len([t for t in all_theories if t.lifecycle == "active"])

        scope_counts = {}
        for theory in all_theories:
            scope_counts[theory.scope] = scope_counts.get(theory.scope, 0) + 1

        avg_posterior = (
            sum(t.posterior for t in all_theories) / total_theories
            if total_theories > 0
            else 0
        )

        return {
            "total_theories": total_theories,
            "active_theories": active_theories,
            "scope_distribution": scope_counts,
            "average_posterior": round(avg_posterior, 3),
            "support_classes": {
                "strong": len([t for t in all_theories if t.support_class == "strong"]),
                "moderate": len(
                    [t for t in all_theories if t.support_class == "moderate"]
                ),
                "weak": len([t for t in all_theories if t.support_class == "weak"]),
            },
        }

    def _theory_to_dict(self, theory: TheoryMetadata) -> Dict[str, Any]:
        """Convert theory metadata to dictionary"""
        return {
            "id": theory.id,
            "version": theory.version,
            "title": theory.title,
            "scope": theory.scope,
            "lifecycle": theory.lifecycle,
            "author": theory.author,
            "created_at": theory.created_at,
            "updated_at": theory.updated_at,
            "evidence_count": theory.evidence_count,
            "posterior": theory.posterior,
            "support_class": theory.support_class,
            "tags": theory.tags,
            "has_comments": theory.has_comments,
        }
