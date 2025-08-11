from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class EvidenceRecord:
    """Single piece of evidence for a theory"""

    theory_id: str
    theory_version: str
    family_id: str
    bayes_factor: float
    evidence_type: str
    weight: float
    timestamp: str
    source: str


@dataclass
class AccumulationResult:
    """Result of evidence accumulation"""

    theory_id: str
    version: str
    prior: float
    accumulated_bf: float
    posterior: float
    support_class: str
    evidence_count: int
    families_analyzed: int


class EvidenceAccumulator:
    """Accumulates evidence across multiple families using Bayesian updating"""

    def __init__(self):
        self.evidence_store: Dict[str, List[EvidenceRecord]] = {}
        self.support_thresholds = {"weak": 1.0, "moderate": 3.0, "strong": 10.0}

    def add_evidence(
        self,
        theory_id: str,
        theory_version: str,
        family_id: str,
        bayes_factor: float,
        evidence_type: str = "execution",
        weight: float = 1.0,
        source: str = "theory_execution",
    ) -> None:
        """Add new evidence for a theory"""
        key = f"{theory_id}@{theory_version}"

        if key not in self.evidence_store:
            self.evidence_store[key] = []

        evidence = EvidenceRecord(
            theory_id=theory_id,
            theory_version=theory_version,
            family_id=family_id,
            bayes_factor=bayes_factor,
            evidence_type=evidence_type,
            weight=weight,
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=source,
        )

        self.evidence_store[key].append(evidence)

    def update_posterior(
        self, theory_id: str, theory_version: str, prior: float = 0.1
    ) -> AccumulationResult:
        """Calculate updated posterior from all accumulated evidence"""
        key = f"{theory_id}@{theory_version}"
        evidence_list = self.evidence_store.get(key, [])

        if not evidence_list:
            return AccumulationResult(
                theory_id=theory_id,
                version=theory_version,
                prior=prior,
                accumulated_bf=1.0,
                posterior=prior,
                support_class="insufficient",
                evidence_count=0,
                families_analyzed=0,
            )

        # Calculate accumulated Bayes factor (product of individual BFs)
        accumulated_bf = 1.0
        unique_families = set()

        for evidence in evidence_list:
            # Apply shrinkage for small sample sizes
            shrinkage_factor = self._calculate_shrinkage(len(evidence_list))
            weighted_bf = (
                1.0 + (evidence.bayes_factor - 1.0) * evidence.weight * shrinkage_factor
            )
            accumulated_bf *= max(weighted_bf, 0.01)  # Prevent zero BF
            unique_families.add(evidence.family_id)

        # Calculate posterior using Bayes' theorem
        posterior = self._calculate_posterior(prior, accumulated_bf)

        # Classify support
        support_class = self._classify_support(accumulated_bf)

        return AccumulationResult(
            theory_id=theory_id,
            version=theory_version,
            prior=prior,
            accumulated_bf=accumulated_bf,
            posterior=posterior,
            support_class=support_class,
            evidence_count=len(evidence_list),
            families_analyzed=len(unique_families),
        )

    def get_evidence_trail(
        self, theory_id: str, theory_version: str
    ) -> List[Dict[str, Any]]:
        """Get audit trail of all evidence for a theory"""
        key = f"{theory_id}@{theory_version}"
        evidence_list = self.evidence_store.get(key, [])

        return [
            {
                "family_id": e.family_id,
                "bayes_factor": e.bayes_factor,
                "evidence_type": e.evidence_type,
                "weight": e.weight,
                "timestamp": e.timestamp,
                "source": e.source,
            }
            for e in evidence_list
        ]

    def _calculate_shrinkage(self, sample_size: int) -> float:
        """Apply shrinkage factor for small sample sizes"""
        if sample_size >= 10:
            return 1.0
        elif sample_size >= 5:
            return 0.8
        elif sample_size >= 2:
            return 0.6
        else:
            return 0.4

    def _calculate_posterior(self, prior: float, bayes_factor: float) -> float:
        """Calculate posterior probability using Bayes' theorem"""
        numerator = prior * bayes_factor
        denominator = numerator + (1 - prior)
        return numerator / denominator if denominator > 0 else 0.0

    def _classify_support(self, bayes_factor: float) -> str:
        """Classify evidence support based on accumulated Bayes factor"""
        if bayes_factor >= self.support_thresholds["strong"]:
            return "strong"
        elif bayes_factor >= self.support_thresholds["moderate"]:
            return "moderate"
        elif bayes_factor >= self.support_thresholds["weak"]:
            return "weak"
        else:
            return "insufficient"
