from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class AnchorSequence(BaseModel):
    id: str
    sequence_hash: str
    reference_genome: str = "GRCh38"
    quality_score: float
    usage_count: int = 0
    created_at: datetime


class GenomicDifference(BaseModel):
    id: str
    anchor_id: str
    individual_id: str
    position: int
    reference_allele: str
    alternate_allele: str
    quality_score: float
    created_at: datetime


class GenomicDataRequest(BaseModel):
    individual_id: str
    vcf_data: str
    reference_genome: str = "GRCh38"


class GenomicDataResponse(BaseModel):
    individual_id: str
    anchor_id: str
    total_variants: int
    storage_size_mb: float
    compression_ratio: float
