"""
Decision API Endpoints (Day 5)
Exposes POST /api/decision/recommend to evaluate events, score candidate actions,
and return deterministic recovery decisions.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.db import get_db
from backend.services.decision_engine import decision_engine_service, DecisionResult
from database.decision_models import get_recovery_decision_by_event_id

router = APIRouter()


class DecisionRecommendRequest(BaseModel):
    """Payload for requesting a recovery action decision."""
    event_id: Optional[str] = Field(None, json_schema_extra={"example": "evt_000666"})
    event_data: Optional[Dict[str, Any]] = Field(None, description="Optional raw or processed event dict.")
    policy_overrides: Optional[Dict[str, Any]] = Field(None, description="Optional merchant policy overrides.")


class AlternativeActionResponse(BaseModel):
    action: str
    score: float
    expected_recovery_value: Optional[float] = None
    estimated_recovery_probability: Optional[float] = None
    friction_level: Optional[str] = None


class ExcludedActionResponse(BaseModel):
    action: str
    reason: str


class DecisionRecommendResponse(BaseModel):
    """
    Standardized response payload for Recovery Decision recommendation.
    """
    decision_id: str
    event_id: str
    customer_id: str
    risk_score: float
    priority: str
    selected_action: str
    decision_score: float
    expected_recovery_value: float
    estimated_recovery_probability: float
    explanation: str
    reasons: List[str]
    alternatives: List[Dict[str, Any]]
    excluded_actions: List[Dict[str, str]]
    ai_recommendation: Optional[Dict[str, Any]] = None
    divergence_reason: Optional[str] = None
    policy_applied: Dict[str, Any] = Field(default_factory=dict)


@router.post(
    "/recommend",
    response_model=DecisionRecommendResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend Recovery Action (Day 5 Decision Engine)",
    description="Deterministically combines AI diagnosis, expected value, customer friction, action cost, and merchant policy to select the optimal recovery action."
)
async def recommend_recovery_action_endpoint(
    request: DecisionRecommendRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates checkout abandonment event and makes authoritative recovery action decision:
    1. Runs deterministic risk engine & AI diagnosis
    2. Filters candidate actions based on eligibility and merchant policy
    3. Scores actions: Action Score = Expected Recovery Value − Friction − Cost − Penalty (0-100)
    4. Selects best action adhering to merchant policy thresholds
    5. Explains decision and flags any divergence against AI suggestion
    6. Persists decision in database audit trail
    """
    try:
        event_payload = request.event_data if request.event_data is not None else request.event_id
        if not event_payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'event_id' or 'event_data' must be provided in request payload."
            )

        decision_result: DecisionResult = await decision_engine_service.decide_recovery_action(
            event_data=event_payload,
            policy_overrides=request.policy_overrides,
            db=db,
        )

        res_dict = decision_result.to_dict()
        # Ensure alternatives format matches spec
        alternatives_formatted = [
            {
                "action": alt["action"],
                "score": alt["score"],
                "expected_recovery_value": alt.get("expected_recovery_value"),
                "estimated_recovery_probability": alt.get("estimated_recovery_probability"),
                "friction_level": alt.get("friction_level"),
            }
            for alt in res_dict.get("alternative_actions", [])
        ]

        return DecisionRecommendResponse(
            decision_id=res_dict["decision_id"],
            event_id=res_dict["event_id"],
            customer_id=res_dict["customer_id"],
            risk_score=res_dict["risk_score"],
            priority=res_dict["priority"],
            selected_action=res_dict["selected_action"],
            decision_score=res_dict["decision_score"],
            expected_recovery_value=res_dict["expected_recovery_value"],
            estimated_recovery_probability=res_dict["estimated_recovery_probability"],
            explanation=res_dict["explanation"],
            reasons=res_dict["reasons"],
            alternatives=alternatives_formatted,
            excluded_actions=res_dict.get("excluded_actions", []),
            ai_recommendation=res_dict.get("ai_recommendation"),
            divergence_reason=res_dict.get("divergence_reason"),
            policy_applied=res_dict.get("policy_applied", {}),
        )

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decision Engine failed: {str(e)}"
        )


@router.get(
    "/decisions/{event_id}",
    summary="Get Historical Recovery Decision for Event",
    description="Retrieves the persisted Decision Engine decision record for a given event ID."
)
def get_recovery_decision_endpoint(event_id: str, db: Session = Depends(get_db)):
    record = get_recovery_decision_by_event_id(db, event_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No recovery decision found for event_id '{event_id}'."
        )
    return record.to_dict()
