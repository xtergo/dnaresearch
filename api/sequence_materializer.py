from typing import Dict, List

from anchor_diff import AnchorDiffStorage
from models import GenomicDifference


class SequenceMaterializer:
    """Materialize full genomic sequences from anchor+diff storage"""

    # Reconstructs individual sequences from compressed anchor+diff format

    def __init__(self, storage: AnchorDiffStorage):
        self.storage = storage

    def materialize_sequence(self, individual_id: str, anchor_id: str) -> str:
        """Reconstruct full genomic sequence from anchor and diffs"""
        # Get anchor sequence
        anchor = self.storage.anchors.get(anchor_id)
        if not anchor:
            raise ValueError(f"Anchor {anchor_id} not found")

        # Get differences for this individual
        individual_diffs = [
            diff
            for diff in self.storage.diffs.get(anchor_id, [])
            if diff.individual_id == individual_id
        ]

        # Start with reference sequence (simplified - using anchor hash as base)
        base_sequence = self._get_reference_sequence(anchor.sequence_hash)

        # Apply differences to reconstruct individual sequence
        materialized = self._apply_differences(base_sequence, individual_diffs)

        return materialized

    def _get_reference_sequence(self, sequence_hash: str) -> str:
        """Get reference sequence from hash (simplified implementation)"""
        # In real implementation, this would fetch from reference genome
        # For demo, generate a mock sequence based on hash
        return "ATCG" * 100  # 400bp mock sequence

    def _apply_differences(
        self, base_sequence: str, diffs: List[GenomicDifference]
    ) -> str:
        """Apply genomic differences to base sequence"""
        sequence = list(base_sequence)

        # Sort diffs by position (reverse order to avoid index shifting)
        sorted_diffs = sorted(diffs, key=lambda d: d.position, reverse=True)

        for diff in sorted_diffs:
            pos = diff.position - 1  # Convert to 0-based indexing

            if pos < len(sequence):
                # Simple substitution (real implementation would handle indels)
                if len(diff.reference_allele) == 1 and len(diff.alternate_allele) == 1:
                    sequence[pos] = diff.alternate_allele

        return "".join(sequence)

    def get_materialization_stats(self, individual_id: str, anchor_id: str) -> Dict:
        """Get statistics about sequence materialization"""
        anchor = self.storage.anchors.get(anchor_id)
        if not anchor:
            return {"error": "Anchor not found"}

        individual_diffs = [
            diff
            for diff in self.storage.diffs.get(anchor_id, [])
            if diff.individual_id == individual_id
        ]

        materialized_sequence = self.materialize_sequence(individual_id, anchor_id)

        return {
            "individual_id": individual_id,
            "anchor_id": anchor_id,
            "reference_genome": anchor.reference_genome,
            "total_variants": len(individual_diffs),
            "sequence_length": len(materialized_sequence),
            "materialization_efficiency": (
                len(individual_diffs) / len(materialized_sequence)
                if materialized_sequence
                else 0
            ),
        }
