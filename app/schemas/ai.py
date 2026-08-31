from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AIAnalysisRequest(BaseModel):
    customer_name: str = Field(..., json_schema_extra={"example": "Acme Corp"})
    overdue_days: int = Field(..., json_schema_extra={"example": 15})
    amount: float = Field(..., json_schema_extra={"example": 12500.00})
    currency: str = Field("INR", json_schema_extra={"example": "INR"})
    previous_communications: Optional[List[str]] = Field(default_factory=list)


class AIAnalysisResponse(BaseModel):
    risk_level: str = Field(..., json_schema_extra={"example": "low"})  # low, medium, high
    recommended_action: str = Field(..., json_schema_extra={"example": "friendly_reminder"})
    suggested_channel: str = Field(..., json_schema_extra={"example": "email"})  # email, sms, whatsapp
    personalized_draft: str = Field(..., json_schema_extra={"example": "Dear Acme Corp team, we noticed invoice #102 is pending..."})
    confidence_score: float = Field(..., json_schema_extra={"example": 0.92})
