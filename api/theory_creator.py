"""Theory creation and management"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class TheoryCreationResult:
    theory_id: str
    version: str
    status: str
    validation_errors: list
    created_at: str


class TheoryCreator:
    """Handle theory creation and validation"""

    def __init__(self):
        self.created_theories = {}  # In production, this would be a database

    def create_theory(
        self, theory_data: Dict[str, Any], author: str = "anonymous"
    ) -> TheoryCreationResult:
        """Create a new theory"""

        # Generate theory ID if not provided
        if "id" not in theory_data:
            theory_data["id"] = self._generate_theory_id(
                theory_data.get("scope", "general")
            )

        # Set default version if not provided
        if "version" not in theory_data:
            theory_data["version"] = "1.0.0"

        # Add metadata
        theory_data["created_at"] = datetime.utcnow().isoformat() + "Z"
        theory_data["updated_at"] = theory_data["created_at"]
        theory_data["author"] = author
        theory_data["lifecycle"] = "draft"

        # Validate theory structure
        validation_errors = self._validate_theory_structure(theory_data)

        if validation_errors:
            return TheoryCreationResult(
                theory_id=theory_data["id"],
                version=theory_data["version"],
                status="validation_failed",
                validation_errors=validation_errors,
                created_at=theory_data["created_at"],
            )

        # Store theory
        theory_key = f"{theory_data['id']}@{theory_data['version']}"
        self.created_theories[theory_key] = theory_data

        return TheoryCreationResult(
            theory_id=theory_data["id"],
            version=theory_data["version"],
            status="created",
            validation_errors=[],
            created_at=theory_data["created_at"],
        )

    def update_theory(
        self,
        theory_id: str,
        version: str,
        updates: Dict[str, Any],
        author: str = "anonymous",
    ) -> TheoryCreationResult:
        """Update an existing theory"""

        theory_key = f"{theory_id}@{version}"
        if theory_key not in self.created_theories:
            return TheoryCreationResult(
                theory_id=theory_id,
                version=version,
                status="not_found",
                validation_errors=["Theory not found"],
                created_at="",
            )

        # Get existing theory
        theory_data = self.created_theories[theory_key].copy()

        # Apply updates
        theory_data.update(updates)
        theory_data["updated_at"] = datetime.utcnow().isoformat() + "Z"
        theory_data["author"] = author

        # Validate updated theory
        validation_errors = self._validate_theory_structure(theory_data)

        if validation_errors:
            return TheoryCreationResult(
                theory_id=theory_id,
                version=version,
                status="validation_failed",
                validation_errors=validation_errors,
                created_at=theory_data.get("created_at", ""),
            )

        # Store updated theory
        self.created_theories[theory_key] = theory_data

        return TheoryCreationResult(
            theory_id=theory_id,
            version=version,
            status="updated",
            validation_errors=[],
            created_at=theory_data["created_at"],
        )

    def get_theory(self, theory_id: str, version: str) -> Optional[Dict[str, Any]]:
        """Get a created theory"""
        theory_key = f"{theory_id}@{version}"
        return self.created_theories.get(theory_key)

    def delete_theory(self, theory_id: str, version: str) -> bool:
        """Delete a theory"""
        theory_key = f"{theory_id}@{version}"
        if theory_key in self.created_theories:
            del self.created_theories[theory_key]
            return True
        return False

    def get_theory_template(self, scope: str = "autism") -> Dict[str, Any]:
        """Get a theory template for the specified scope"""
        templates = {
            "autism": {
                "id": "",
                "version": "1.0.0",
                "scope": "autism",
                "title": "New Autism Theory",
                "description": "Description of the theory",
                "criteria": {
                    "genes": ["SHANK3"],
                    "pathways": ["synaptic_transmission"],
                    "phenotypes": ["autism_spectrum_disorder"],
                },
                "evidence_model": {
                    "priors": 0.1,
                    "likelihood_weights": {
                        "variant_hit": 2.0,
                        "segregation": 1.5,
                        "pathway": 1.0,
                    },
                },
                "tags": ["draft", "new"],
            },
            "cancer": {
                "id": "",
                "version": "1.0.0",
                "scope": "cancer",
                "title": "New Cancer Theory",
                "description": "Description of the theory",
                "criteria": {
                    "genes": ["BRCA1"],
                    "pathways": ["dna_repair"],
                    "phenotypes": ["breast_cancer"],
                },
                "evidence_model": {
                    "priors": 0.05,
                    "likelihood_weights": {
                        "variant_hit": 3.0,
                        "segregation": 2.0,
                        "pathway": 1.5,
                    },
                },
                "tags": ["draft", "new"],
            },
        }

        return templates.get(scope, templates["autism"])

    def _generate_theory_id(self, scope: str) -> str:
        """Generate a unique theory ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{scope}-theory-{timestamp}"

    def _validate_theory_structure(self, theory_data: Dict[str, Any]) -> list:
        """Validate theory structure"""
        errors = []

        # Required fields
        required_fields = ["id", "version", "scope", "criteria", "evidence_model"]
        for field in required_fields:
            if field not in theory_data:
                errors.append(f"Missing required field: {field}")

        # Validate scope
        valid_scopes = [
            "autism",
            "cancer",
            "cardiovascular",
            "neurological",
            "metabolic",
        ]
        if "scope" in theory_data and theory_data["scope"] not in valid_scopes:
            errors.append(f"Invalid scope. Must be one of: {', '.join(valid_scopes)}")

        # Validate version format
        if "version" in theory_data:
            version = theory_data["version"]
            if not self._is_valid_semver(version):
                errors.append(
                    "Version must be in semantic version format (e.g., 1.0.0)"
                )

        # Validate evidence model
        if "evidence_model" in theory_data:
            evidence_model = theory_data["evidence_model"]
            if not isinstance(evidence_model, dict):
                errors.append("Evidence model must be an object")
            else:
                if "priors" not in evidence_model:
                    errors.append("Evidence model missing 'priors' field")
                elif not (0 <= evidence_model["priors"] <= 1):
                    errors.append("Priors must be between 0 and 1")

                if "likelihood_weights" not in evidence_model:
                    errors.append("Evidence model missing 'likelihood_weights' field")

        # Validate criteria
        if "criteria" in theory_data:
            criteria = theory_data["criteria"]
            if not isinstance(criteria, dict):
                errors.append("Criteria must be an object")
            elif not any(
                key in criteria for key in ["genes", "pathways", "phenotypes"]
            ):
                errors.append(
                    "Criteria must contain at least one of: genes, pathways, phenotypes"
                )

        return errors

    def _is_valid_semver(self, version: str) -> bool:
        """Check if version is valid semantic version"""
        import re

        pattern = r"^\d+\.\d+\.\d+$"
        return bool(re.match(pattern, version))
