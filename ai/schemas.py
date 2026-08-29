"""
Pydantic Schemas and Controlled Enums for RecoverAI AI Diagnosis Agent (Day 4)
Enforces strict structured outputs, validation bounds, and enum categories.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class DiagnosisCategory(str, Enum):
    """Controlled root cause diagnosis categories."""
    HIGH_PURCHASE_INTENT_ABANDONMENT = "HIGH_PURCHASE_INTENT_ABANDONMENT"
    REPEAT_CUSTOMER_ABANDONMENT = "REPEAT_CUSTOMER_ABANDONMENT"
    HIGH_VALUE_ABANDONMENT = "HIGH_VALUE_ABANDONMENT"
    LOW_INTENT_ABANDONMENT = "LOW_INTENT_ABANDONMENT"
    RECENT_CHECKOUT_DROP = "RECENT_CHECKOUT_DROP"
    LOW_RECOVERY_CONFIDENCE = "LOW_RECOVERY_CONFIDENCE"


class RecoveryAction(str, Enum):
    """Controlled least-intrusive recovery actions."""
    CHECKOUT_REMINDER = "CHECKOUT_REMINDER"
    PERSONALIZED_REMINDER = "PERSONALIZED_REMINDER"
    PAYMENT_LINK = "PAYMENT_LINK"
    DELAYED_FOLLOW_UP = "DELAYED_FOLLOW_UP"
    NO_ACTION = "NO_ACTION"
    ESCALATE = "ESCALATE"


class PriorityTier(str, Enum):
    """Urgency priority tiers matching Day 3 Risk Engine."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AIDiagnosisResult(BaseModel):
    """
    Structured response payload returned by LLM and validated by Pydantic.
    """
    diagnosis: DiagnosisCategory = Field(
        ...,
        description="Controlled classification of why the checkout/payment was not completed."
    )
    recovery_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI-estimated recovery probability (0.00 to 1.00)."
    )
    recommended_action: RecoveryAction = Field(
        ...,
        description="Controlled least-intrusive recovery intervention."
    )
    priority: PriorityTier = Field(
        ...,
        description="Operational urgency priority tier."
    )
    recommendation_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence in this recommendation (0.00 to 1.00)."
    )
    reason_codes: List[str] = Field(
        default_factory=list,
        description="Standardized machine-readable explanation tags."
    )
    explanation: str = Field(
        ...,
        min_length=10,
        description="Concise rationale explaining the diagnosis and chosen action."
    )
    suggested_message: str = Field(
        ...,
        description="Customer-facing communication draft tailored to this event."
    )

    @field_validator("recovery_probability", "recommendation_confidence")
    @classmethod
    def validate_probabilities(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Probability/confidence must be strictly between 0.0 and 1.0, got {v}")
        return round(float(v), 2)


class AIDecisionContext(BaseModel):
    """
    Comprehensive context payload supplied to the LLM.
    Combines event telemetry, customer history, and Day 3 deterministic risk output.
    """
    # Event Identifiers & Telemetry
    event_id: str
    customer_id: str
    session_id: Optional[str] = None
    cart_value: float
    currency: str = "INR"
    payment_method: str = "UPI"
    session_duration: int
    pages_viewed: int
    purchase_status: str = "abandoned"

    # Customer Historical Aggregates (Day 2)
    previous_purchases: int
    customer_lifetime_value: float
    average_order_value: float = 0.0
    cart_abandonment_rate: float = 0.0
    total_sessions: int = 1

    # Deterministic Risk Engine Metrics (Day 3 - Read-Only Inputs)
    risk_score: float
    priority: str
    purchase_intent_score: float
    revenue_at_risk: float
    expected_recoverable_revenue: float


class DiagnoseEventRequest(BaseModel):
    """API request payload for diagnosing an event."""
    event_id: Optional[str] = Field(None, json_schema_extra={"example": "evt_000666"})
    event_data: Optional[Dict[str, Any]] = Field(None, description="Optional raw or processed event dict for direct evaluation.")


class DiagnoseEventResponse(BaseModel):
    """API response envelope containing diagnosis, financial metrics, and audit metadata."""
    event_id: str
    customer_id: str
    diagnosis: DiagnosisCategory
    recovery_probability: float = Field(..., description="AI-estimated recovery probability (0.00-1.00)")
    expected_recovery_value: float = Field(..., description="Calculated as revenue_at_risk * recovery_probability in INR")
    revenue_at_risk: float
    recommended_action: RecoveryAction
    priority: PriorityTier
    recommendation_confidence: float
    reason_codes: List[str]
    explanation: str
    suggested_message: str
    source: str = Field("ai", description="'ai' for LLM generation or 'fallback' for deterministic fallback")
    model_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
