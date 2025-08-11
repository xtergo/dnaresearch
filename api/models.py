from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

class Anchor(BaseModel):
    id: str
    sequence_hash: str
    reference_genome: str
    quality_score: float
    usage_count: int
    created_at: datetime
    
class GenomicDiff(BaseModel):
    id: str
    anchor_id: str
    individual_id: str
    position: int
    reference_allele: str
    alternate_allele: str
    quality_score: float
    created_at: datetime

class GenomicData(BaseModel):
    individual_id: str
    anchor_id: str
    diffs: List[GenomicDiff]
    total_variants: int
    storage_size_mb: float