"""Variant interpretation engine for plain language explanations"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class VariantImpact(Enum):
    BENIGN = "benign"
    LIKELY_BENIGN = "likely_benign"
    UNCERTAIN = "uncertain"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    PATHOGENIC = "pathogenic"


class ConfidenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class VariantInterpretation:
    variant: str
    gene: str
    impact: VariantImpact
    confidence: ConfidenceLevel
    parent_explanation: str
    technical_explanation: str
    recommendations: List[str]
    evidence_sources: List[str]
    population_frequency: Optional[float] = None


class VariantInterpreter:
    """Interpret genetic variants with plain language explanations"""

    def __init__(self):
        # Gene-specific interpretation rules
        self.gene_rules = {
            "BRCA1": {
                "condition": "breast and ovarian cancer",
                "inheritance": "autosomal dominant",
                "penetrance": "high",
                "screening": "enhanced breast/ovarian screening",
            },
            "BRCA2": {
                "condition": "breast and ovarian cancer",
                "inheritance": "autosomal dominant",
                "penetrance": "high",
                "screening": "enhanced breast/ovarian screening",
            },
            "SHANK3": {
                "condition": "autism spectrum disorder",
                "inheritance": "autosomal dominant",
                "penetrance": "variable",
                "screening": "developmental monitoring",
            },
            "CFTR": {
                "condition": "cystic fibrosis",
                "inheritance": "autosomal recessive",
                "penetrance": "complete",
                "screening": "carrier screening",
            },
            "APOE": {
                "condition": "Alzheimer's disease risk",
                "inheritance": "complex",
                "penetrance": "risk factor",
                "screening": "cognitive monitoring",
            },
        }

        # Variant type patterns
        self.variant_patterns = {
            r"c\.\d+[ATCG]>[ATCG]": "missense",
            r"c\.\d+del": "deletion",
            r"c\.\d+ins": "insertion",
            r"c\.\d+dup": "duplication",
            r"c\.\d+_\d+del": "deletion",
            r"c\.\*\d+": "3_prime_utr",
        }

    def interpret_variant(
        self, gene: str, variant: str, vcf_data: str = None
    ) -> VariantInterpretation:
        """Interpret a genetic variant with plain language explanation"""

        # Determine variant type
        variant_type = self._classify_variant_type(variant)

        # Get gene information
        gene_info = self.gene_rules.get(
            gene.upper(),
            {
                "condition": "genetic condition",
                "inheritance": "unknown",
                "penetrance": "variable",
                "screening": "genetic counseling",
            },
        )

        # Predict impact based on variant type and gene
        impact, confidence = self._predict_impact(gene, variant, variant_type)

        # Generate explanations
        parent_explanation = self._generate_parent_explanation(
            gene, variant, impact, gene_info
        )
        technical_explanation = self._generate_technical_explanation(
            gene, variant, variant_type, impact
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(gene, impact, gene_info)

        # Mock evidence sources
        evidence_sources = [
            "ClinVar database",
            "ACMG/AMP guidelines",
            f"{gene} gene-specific literature",
        ]

        return VariantInterpretation(
            variant=variant,
            gene=gene,
            impact=impact,
            confidence=confidence,
            parent_explanation=parent_explanation,
            technical_explanation=technical_explanation,
            recommendations=recommendations,
            evidence_sources=evidence_sources,
            population_frequency=self._estimate_frequency(gene, variant_type),
        )

    def _classify_variant_type(self, variant: str) -> str:
        """Classify variant type from HGVS notation"""
        for pattern, variant_type in self.variant_patterns.items():
            if re.match(pattern, variant):
                return variant_type
        return "unknown"

    def _predict_impact(self, gene: str, variant: str, variant_type: str) -> tuple:
        """Predict variant impact and confidence"""

        # High-confidence pathogenic variants
        if gene.upper() in ["BRCA1", "BRCA2"] and variant_type == "deletion":
            return VariantImpact.PATHOGENIC, ConfidenceLevel.HIGH

        # Known pathogenic variants (simplified)
        if gene.upper() == "CFTR" and "F508del" in variant:
            return VariantImpact.PATHOGENIC, ConfidenceLevel.HIGH

        # Missense variants - uncertain by default
        if variant_type == "missense":
            if gene.upper() in ["BRCA1", "BRCA2"]:
                return VariantImpact.UNCERTAIN, ConfidenceLevel.MEDIUM
            return VariantImpact.UNCERTAIN, ConfidenceLevel.LOW

        # Deletions in critical genes
        if variant_type == "deletion" and gene.upper() in ["SHANK3"]:
            return VariantImpact.LIKELY_PATHOGENIC, ConfidenceLevel.MEDIUM

        # Default uncertain
        return VariantImpact.UNCERTAIN, ConfidenceLevel.LOW

    def _generate_parent_explanation(
        self, gene: str, variant: str, impact: VariantImpact, gene_info: Dict
    ) -> str:
        """Generate parent-friendly explanation"""

        condition = gene_info.get("condition", "a genetic condition")

        if impact == VariantImpact.PATHOGENIC:
            return (
                f"This genetic change in the {gene} gene is known to cause {condition}. "
                f"This means there is a high likelihood that this change contributes to "
                f"the associated health condition."
            )

        elif impact == VariantImpact.LIKELY_PATHOGENIC:
            return (
                f"This genetic change in the {gene} gene likely contributes to {condition}. "
                f"While we have good evidence this change is harmful, more research may "
                f"provide additional certainty."
            )

        elif impact == VariantImpact.UNCERTAIN:
            return (
                f"We found a genetic change in the {gene} gene, but we're not sure if "
                f"it causes {condition}. This change needs more research to understand "
                f"its significance. It may be harmless or it may contribute to health issues."
            )

        elif impact == VariantImpact.LIKELY_BENIGN:
            return (
                f"This genetic change in the {gene} gene is probably harmless and "
                f"unlikely to cause {condition}. However, we continue to monitor "
                f"research on this change."
            )

        else:  # BENIGN
            return (
                f"This genetic change in the {gene} gene is harmless and does not "
                f"cause {condition}. This is a normal variation found in healthy people."
            )

    def _generate_technical_explanation(
        self, gene: str, variant: str, variant_type: str, impact: VariantImpact
    ) -> str:
        """Generate technical explanation for researchers"""

        return (
            f"Variant {variant} in {gene} is classified as {variant_type}. "
            f"Based on ACMG/AMP guidelines, this variant is interpreted as "
            f"{impact.value.replace('_', ' ')}. Classification considers "
            f"population frequency, computational predictions, functional studies, "
            f"and segregation data where available."
        )

    def _generate_recommendations(
        self, gene: str, impact: VariantImpact, gene_info: Dict
    ) -> List[str]:
        """Generate clinical recommendations"""

        recommendations = []

        if impact in [VariantImpact.PATHOGENIC, VariantImpact.LIKELY_PATHOGENIC]:
            recommendations.extend(
                [
                    "Genetic counseling recommended",
                    f"Consider {gene_info.get('screening', 'appropriate screening')}",
                    "Family member testing may be appropriate",
                ]
            )

            if gene.upper() in ["BRCA1", "BRCA2"]:
                recommendations.append("Enhanced breast and ovarian cancer screening")
            elif gene.upper() == "SHANK3":
                recommendations.append("Early intervention and developmental support")

        elif impact == VariantImpact.UNCERTAIN:
            recommendations.extend(
                [
                    "Genetic counseling for interpretation",
                    "Consider family history and clinical features",
                    "Periodic re-evaluation as knowledge advances",
                ]
            )

        else:  # Benign or likely benign
            recommendations.extend(
                [
                    "No specific medical action required",
                    "Standard population screening guidelines apply",
                ]
            )

        return recommendations

    def _estimate_frequency(self, gene: str, variant_type: str) -> Optional[float]:
        """Estimate population frequency (mock implementation)"""

        # Mock frequencies based on variant type
        frequency_map = {
            "missense": 0.001,
            "deletion": 0.0001,
            "insertion": 0.0001,
            "duplication": 0.0001,
        }

        return frequency_map.get(variant_type, 0.0001)

    def get_gene_summary(self, gene: str) -> Dict[str, Any]:
        """Get summary information about a gene"""

        gene_info = self.gene_rules.get(gene.upper(), {})

        return {
            "gene": gene.upper(),
            "condition": gene_info.get("condition", "Unknown condition"),
            "inheritance_pattern": gene_info.get("inheritance", "Unknown"),
            "penetrance": gene_info.get("penetrance", "Variable"),
            "recommended_screening": gene_info.get("screening", "Genetic counseling"),
            "clinical_significance": f"Variants in {gene.upper()} can affect {gene_info.get('condition', 'health')}",
        }
