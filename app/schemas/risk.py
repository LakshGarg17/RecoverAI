"""
Pydantic Schemas for RecoverAI Revenue Risk Engine (Day 3)
Defines risk score breakdown, single event risk evaluations, and aggregate summaries.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class RiskScoreBreakdown(BaseModel):
    """Component sub-scores contributing to the blended risk score."""
    cart_value_score: float = Field(..., ge=0.0, le=100.0, description="Cart/Order value score (weight: 25%)")
    purchase_intent_score: float = Field(..., ge=0.0, le=100.0, description="Observed purchase intent score (weight: 30%)")
    customer_history_score: float = Field(..., ge=0.0, le=100.0, description="Customer loyalty and spend history score (weight: 20%)")
    engagement_score: float = Field(..., ge=0.0, le=100.0, description="Session engagement and exploration score (weight: 15%)")
    recency_score: float = Field(..., ge=0.0, le=100.0, description="Time recency decay score (weight: 10%)")


class RiskEvaluationRequest(BaseModel):
    """Payload representing a single RecoverAI event for risk scoring."""
    event_id: str = Field(..., json_schema_extra={"example": "evt_001024"})
    customer_id: str = Field(..., json_schema_extra={"example": "cust_01803"})
    session_id: Optional[str] = Field(None, json_schema_extra={"example": "sess_001024"})
    amount: float = Field(..., ge=0.0, json_schema_extra={"example": 14999.00})
    currency: str = Field("INR", json_schema_extra={"example": "INR"})
    payment_method: Optional[str] = Field("UPI", json_schema_extra={"example": "UPI"})
    event_type: str = Field("cart_abandoned", json_schema_extra={"example": "cart_abandoned"})
    purchase_status: str = Field("abandoned", json_schema_extra={"example": "abandoned"})
    cart_value: float = Field(..., ge=0.0, json_schema_extra={"example": 14999.00})
    session_duration: int = Field(0, ge=0, json_schema_extra={"example": 1200})
    pages_viewed: int = Field(1, ge=1, json_schema_extra={"example": 18})
    purchase_history: int = Field(0, ge=0, json_schema_extra={"example": 3})
    customer_lifetime_value: float = Field(0.0, ge=0.0, json_schema_extra={"example": 5400.00})
    purchase_intent_score: Optional[float] = Field(None, ge=0.0, le=100.0, json_schema_extra={"example": 85.0})
    revenue_at_risk: Optional[float] = Field(None, ge=0.0, json_schema_extra={"example": 14999.00})
    recency_hours: Optional[float] = Field(None, ge=0.0, json_schema_extra={"example": 2.5})


class RiskEvaluationResponse(BaseModel):
    """Evaluation result produced by the Revenue Risk Engine."""
    event_id: str = Field(..., json_schema_extra={"example": "evt_001024"})
    customer_id: str = Field(..., json_schema_extra={"example": "cust_01803"})
    revenue_at_risk: float = Field(..., ge=0.0, description="Potential Revenue at Risk (raw cart monetary value in INR)")
    expected_recoverable_revenue: float = Field(..., ge=0.0, description="Expected Recoverable Revenue (cart_value * intent_probability)")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Blended risk priority score (0-100)")
    priority: str = Field(..., json_schema_extra={"example": "CRITICAL"}, description="Urgency priority tier: CRITICAL (80-100), HIGH (60-79), MEDIUM (40-59), LOW (0-39)")
    recovery_candidate: bool = Field(..., description="Whether this event represents an active, actionable recovery opportunity")
    score_breakdown: RiskScoreBreakdown = Field(..., description="Detailed component score breakdown")


class PriorityTierSummary(BaseModel):
    """Aggregate statistics for a specific priority tier."""
    tier: str
    event_count: int
    share_percentage: float
    potential_revenue_at_risk: float
    expected_recoverable_revenue: float
    avg_risk_score: float


class RiskBatchSummary(BaseModel):
    """Portfolio-wide aggregate evaluation metrics."""
    total_events_analyzed: int
    recovery_candidates_count: int
    total_potential_revenue_at_risk: float
    total_expected_recoverable_revenue: float
    overall_recovery_efficiency_pct: float
    tier_distribution: Dict[str, PriorityTierSummary]
