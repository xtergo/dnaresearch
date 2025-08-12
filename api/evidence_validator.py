"""Evidence validation module"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class EvidenceValidationResult:
    is_valid: bool
    errors: List[str]
    evidence_type: str
    confidence: float


class EvidenceValidator:
    """Validate evidence data against schemas"""

    def __init__(self):
        self.valid_evidence_types = ["variant_hit", "segregation", "pathway"]
        self.required_fields = ["type", "weight", "timestamp", "data"]

    def validate_evidence(
        self, evidence_data: Dict[str, Any]
    ) -> EvidenceValidationResult:
        """Validate evidence data"""
        errors = []

        # Check required fields
        for field in self.required_fields:
            if field not in evidence_data:
                errors.append(f"Missing required field: {field}")

        # Validate evidence type
        evidence_type = evidence_data.get("type", "")
        if evidence_type not in self.valid_evidence_types:
            errors.append(
                f"Invalid evidence type. Must be one of: {', '.join(self.valid_evidence_types)}"
            )

        # Validate weight range
        weight = evidence_data.get("weight", 0)
        if not isinstance(weight, (int, float)) or weight < 0 or weight > 10:
            errors.append("Weight must be a number between 0 and 10")

        # Validate timestamp format
        timestamp = evidence_data.get("timestamp", "")
        if timestamp:
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                errors.append("Invalid timestamp format")

        # Validate data field
        data = evidence_data.get("data", {})
        if not isinstance(data, dict):
            errors.append("Data field must be an object")

        # Type-specific validation
        if evidence_type == "variant_hit" and isinstance(data, dict):
            required_variant_fields = ["gene", "variant", "impact"]
            for field in required_variant_fields:
                if field not in data:
                    errors.append(
                        f"Variant hit evidence missing required data field: {field}"
                    )

        elif evidence_type == "segregation" and isinstance(data, dict):
            required_segregation_fields = [
                "family_id",
                "affected_carriers",
                "unaffected_carriers",
            ]
            for field in required_segregation_fields:
                if field not in data:
                    errors.append(
                        f"Segregation evidence missing required data field: {field}"
                    )

        elif evidence_type == "pathway" and isinstance(data, dict):
            required_pathway_fields = ["pathway_name", "genes_in_pathway"]
            for field in required_pathway_fields:
                if field not in data:
                    errors.append(
                        f"Pathway evidence missing required data field: {field}"
                    )

        # Calculate confidence
        confidence = evidence_data.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            confidence = 0.5

        return EvidenceValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            evidence_type=evidence_type,
            confidence=confidence,
        )
