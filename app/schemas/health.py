from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ServiceStatus(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    latency_ms: Optional[float] = Field(None, json_schema_extra={"example": 12.5})
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "ok"})
    version: str = Field(..., json_schema_extra={"example": "0.1.0"})
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: str = Field(..., json_schema_extra={"example": "development"})
    services: Dict[str, ServiceStatus] = Field(default_factory=dict)
