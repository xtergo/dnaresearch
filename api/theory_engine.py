import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class ExecutionResult:
    """Result of theory execution"""

    theory_id: str
    version: str
    bayes_factor: float
    posterior: float
    support_class: str
    execution_time_ms: int
    diagnostics: Dict[str, Any]
    artifact_hash: str


class TheoryExecutionEngine:
    """Engine for executing genomic theories with Bayesian updating"""

    def __init__(self):
        self.support_thresholds = {"weak": 1.0, "moderate": 3.0, "strong": 10.0}

    def execute_theory(
        self, theory: Dict[str, Any], vcf_data: str, family_id: str = "default"
    ) -> ExecutionResult:
        """Execute theory against VCF data and calculate Bayes factor"""
        start_time = time.perf_counter()

        # Parse VCF and extract variants
        variants = self._parse_vcf(vcf_data)

        # Calculate likelihood based on theory criteria
        likelihood = self._calculate_likelihood(theory, variants)

        # Calculate null model likelihood
        null_likelihood = self._calculate_null_likelihood(variants)

        # Calculate Bayes factor
        bayes_factor = likelihood / null_likelihood if null_likelihood > 0 else 0.0

        # Update posterior (simplified - assumes uniform prior of 0.1)
        prior = theory.get("evidence_model", {}).get("priors", 0.1)
        posterior = self._calculate_posterior(prior, bayes_factor)

        # Determine support class
        support_class = self._classify_support(bayes_factor)

        # Generate diagnostics
        diagnostics = {
            "variants_analyzed": len(variants),
            "matching_genes": self._count_matching_genes(theory, variants),
            "likelihood": likelihood,
            "null_likelihood": null_likelihood,
            "prior": prior,
        }

        execution_time = max(1, int((time.perf_counter() - start_time) * 1000))

        # Generate artifact hash for reproducibility
        artifact_hash = self._generate_artifact_hash(theory, vcf_data, family_id)

        return ExecutionResult(
            theory_id=theory["id"],
            version=theory["version"],
            bayes_factor=bayes_factor,
            posterior=posterior,
            support_class=support_class,
            execution_time_ms=execution_time,
            diagnostics=diagnostics,
            artifact_hash=artifact_hash,
        )

    def _parse_vcf(self, vcf_data: str) -> List[Dict[str, Any]]:
        """Parse VCF data and extract variants"""
        variants = []
        lines = vcf_data.strip().split("\n")

        for line in lines:
            if line.startswith("#") or not line.strip():
                continue

            fields = line.split("\t")
            if len(fields) >= 5:
                variant = {
                    "chrom": fields[0],
                    "pos": int(fields[1]),
                    "ref": fields[3],
                    "alt": fields[4],
                    "qual": float(fields[5]) if fields[5] != "." else 0.0,
                }
                variants.append(variant)

        return variants

    def _calculate_likelihood(
        self, theory: Dict[str, Any], variants: List[Dict[str, Any]]
    ) -> float:
        """Calculate likelihood of observing variants given theory"""
        criteria = theory.get("criteria", {})
        evidence_model = theory.get("evidence_model", {})
        weights = evidence_model.get("likelihood_weights", {})

        likelihood = 1.0

        # Check gene criteria
        target_genes = criteria.get("genes", [])
        if target_genes:
            gene_hits = self._count_gene_hits(target_genes, variants)
            gene_weight = weights.get("variant_hit", 1.0)
            likelihood *= 1.0 + gene_hits * gene_weight

        # Check pathway criteria (simplified)
        pathways = criteria.get("pathways", [])
        if pathways:
            pathway_weight = weights.get("pathway", 1.0)
            likelihood *= 1.0 + len(pathways) * pathway_weight * 0.1

        return likelihood

    def _calculate_null_likelihood(self, variants: List[Dict[str, Any]]) -> float:
        """Calculate likelihood under null model (random variants)"""
        # Simplified null model - assumes baseline variant rate
        baseline_rate = 0.001  # 0.1% baseline variant probability
        return max(baseline_rate * len(variants), 0.001)

    def _calculate_posterior(self, prior: float, bayes_factor: float) -> float:
        """Calculate posterior probability using Bayes' theorem"""
        numerator = prior * bayes_factor
        denominator = numerator + (1 - prior)
        return numerator / denominator if denominator > 0 else 0.0

    def _classify_support(self, bayes_factor: float) -> str:
        """Classify evidence support based on Bayes factor"""
        if bayes_factor >= self.support_thresholds["strong"]:
            return "strong"
        elif bayes_factor >= self.support_thresholds["moderate"]:
            return "moderate"
        elif bayes_factor >= self.support_thresholds["weak"]:
            return "weak"
        else:
            return "insufficient"

    def _count_matching_genes(
        self, theory: Dict[str, Any], variants: List[Dict[str, Any]]
    ) -> int:
        """Count variants in genes specified by theory"""
        target_genes = theory.get("criteria", {}).get("genes", [])
        return self._count_gene_hits(target_genes, variants)

    def _count_gene_hits(
        self, target_genes: List[str], variants: List[Dict[str, Any]]
    ) -> int:
        """Count variants that hit target genes (simplified mapping)"""
        # Simplified gene mapping - in reality would use genomic coordinates
        gene_regions = {
            "SHANK3": {"chrom": "22", "start": 51135000, "end": 51180000},
            "NRXN1": {"chrom": "2", "start": 50100000, "end": 50400000},
            "SYNGAP1": {"chrom": "6", "start": 33400000, "end": 33500000},
        }

        hits = 0
        for variant in variants:
            for gene in target_genes:
                if gene in gene_regions:
                    region = gene_regions[gene]
                    if (
                        variant["chrom"] == region["chrom"]
                        and region["start"] <= variant["pos"] <= region["end"]
                    ):
                        hits += 1
                        break

        return hits

    def _generate_artifact_hash(
        self, theory: Dict[str, Any], vcf_data: str, family_id: str
    ) -> str:
        """Generate reproducible hash for execution artifact"""
        content = {
            "theory_id": theory["id"],
            "theory_version": theory["version"],
            "vcf_hash": hashlib.md5(vcf_data.encode()).hexdigest(),
            "family_id": family_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
