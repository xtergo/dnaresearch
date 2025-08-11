import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Tuple

from models import AnchorSequence, GenomicDifference


class AnchorDiffStorage:
    """Anchor+Diff storage implementation for genomic data"""

    def __init__(self):
        self.anchors: Dict[str, AnchorSequence] = {}
        self.diffs: Dict[str, List[GenomicDifference]] = {}

    def create_anchor(
        self, sequence_data: str, reference_genome: str = "GRCh38"
    ) -> AnchorSequence:
        """Create anchor sequence from genomic data"""
        sequence_hash = hashlib.sha256(sequence_data.encode()).hexdigest()
        anchor_id = f"anchor-{uuid.uuid4().hex[:8]}"

        # Check if anchor already exists
        for existing_anchor in self.anchors.values():
            if existing_anchor.sequence_hash == sequence_hash:
                existing_anchor.usage_count += 1
                return existing_anchor

        # Create new anchor
        anchor = AnchorSequence(
            id=anchor_id,
            sequence_hash=sequence_hash,
            reference_genome=reference_genome,
            quality_score=0.95,  # Default quality
            usage_count=1,
            created_at=datetime.utcnow(),
        )

        self.anchors[anchor_id] = anchor
        return anchor

    def store_differences(
        self, anchor_id: str, individual_id: str, variants: List[Dict]
    ) -> List[GenomicDifference]:
        """Store genomic differences against anchor"""
        differences = []

        for variant in variants:
            diff_id = f"diff-{uuid.uuid4().hex[:8]}"

            diff = GenomicDifference(
                id=diff_id,
                anchor_id=anchor_id,
                individual_id=individual_id,
                position=variant["position"],
                reference_allele=variant["ref"],
                alternate_allele=variant["alt"],
                quality_score=variant.get("quality", 0.9),
                created_at=datetime.utcnow(),
            )

            differences.append(diff)

        if anchor_id not in self.diffs:
            self.diffs[anchor_id] = []

        self.diffs[anchor_id].extend(differences)
        return differences

    def parse_vcf_variants(self, vcf_data: str) -> List[Dict]:
        """Parse VCF data into variant list"""
        variants = []

        for line in vcf_data.strip().split("\n"):
            if line.startswith("#") or not line.strip():
                continue

            fields = line.split("\t")
            if len(fields) >= 5:
                variants.append(
                    {
                        "position": int(fields[1]),
                        "ref": fields[3],
                        "alt": fields[4],
                        "quality": float(fields[5]) if fields[5] != "." else 0.9,
                    }
                )

        return variants

    def calculate_storage_efficiency(
        self, original_size: int, compressed_size: int
    ) -> Tuple[float, float]:
        """Calculate storage efficiency metrics"""
        storage_mb = compressed_size / (1024 * 1024)
        compression_ratio = (
            original_size / compressed_size if compressed_size > 0 else 1.0
        )

        return storage_mb, compression_ratio

    def process_genomic_data(
        self, individual_id: str, vcf_data: str, reference_genome: str = "GRCh38"
    ) -> Dict:
        """Process genomic data using anchor+diff storage"""
        # Parse variants from VCF
        variants = self.parse_vcf_variants(vcf_data)

        # Create or find anchor
        anchor = self.create_anchor(
            vcf_data[:1000], reference_genome
        )  # Use first 1KB as anchor

        # Store differences
        differences = self.store_differences(anchor.id, individual_id, variants)

        # Calculate storage metrics
        original_size = len(vcf_data.encode())
        compressed_size = len(anchor.sequence_hash) + sum(
            len(str(d.dict())) for d in differences
        )
        storage_mb, compression_ratio = self.calculate_storage_efficiency(
            original_size, compressed_size
        )

        return {
            "individual_id": individual_id,
            "anchor_id": anchor.id,
            "total_variants": len(variants),
            "storage_size_mb": round(storage_mb, 3),
            "compression_ratio": round(compression_ratio, 2),
        }
