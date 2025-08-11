from pydantic import BaseModel
from datetime import datetime

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str