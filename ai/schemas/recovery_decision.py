from pydantic import BaseModel, Field
from typing import Literal, List, Optional


class CustomerRiskProfile(BaseModel):
    risk_level: Literal["low", "medium", "high", "critical"]
    risk_factors: List[str]
    recovery_probability: float = Field(..., ge=0.0, le=1.0)


class RecoveryActionPlan(BaseModel):
    recommended_action: Literal[
        "gentle_reminder",
        "incentivized_recovery",
        "urgent_escalation",
        "pause_service",
        "human_review",
    ]
    preferred_channel: Literal["email", "sms", "whatsapp", "in_app_banner"]
    draft_subject: Optional[str] = None
    draft_message: str
    discount_offered_percent: Optional[int] = 0
    next_check_in_days: int = 3
