"""
End-to-End Recovery Pipeline Endpoint (Day 7)
Exposes POST /api/recovery/run to chain the complete pipeline:
Event -> Risk Engine -> AI Diagnosis -> Decision Engine -> Guardrail Engine -> Execution Engine -> Razorpay Test Mode.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Header, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.db import get_db
from ai.schemas import GuardrailStatus
from backend.services.decision_engine import decision_engine_service, DecisionResult
from backend.services.guardrail_engine import guardrail_engine_service, GuardrailValidationResult
from backend.services.execution_engine import execution_engine_service, ExecutionResult


router = APIRouter()


class RecoveryRunRequest(BaseModel):
    """Payload for executing an end-to-end recovery pipeline."""
    event_id: Optional[str] = Field(None, json_schema_extra={"example": "evt_000666"})
    event_data: Optional[Dict[str, Any]] = Field(None, description="Optional raw or processed event dict.")
    current_purchase_status: Optional[str] = Field(None, description="Live purchase status if known.")
    policy_overrides: Optional[Dict[str, Any]] = Field(None, description="Optional merchant policy overrides.")


class RecoveryRunResponse(BaseModel):
    """Unified response payload from POST /api/recovery/run."""
    event_id: str
    customer_id: Optional[str] = None
    risk_score: float
    priority: Optional[str] = None
    selected_action: str
    decision_score: Optional[float] = None
    guardrail_status: str
    execution_status: str
    expected_recovery_value: float
    payment_link_created: bool
    payment_link_id: Optional[str] = None
    payment_url: Optional[str] = None
    execution_id: Optional[str] = None
    reason: Optional[str] = None
    blocked_reasons: Optional[List[str]] = None


@router.post(
    "/run",
    response_model=RecoveryRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Autonomous Recovery Pipeline (End-to-End)",
    description="Chains Risk Engine -> AI Diagnosis -> Decision Engine -> Guardrail Engine -> Execution Engine in Razorpay Test Mode."
)
async def run_end_to_end_recovery_endpoint(
    request: RecoveryRunRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    """
    Executes complete autonomous recovery lifecycle:
    1. Runs Deterministic Risk Engine + AI Diagnosis + Decision Engine
    2. Enforces 10 safety & policy guardrails
    3. If approved, creates Razorpay Test Mode payment link or internal task
    4. If blocked, returns blocked outcome without calling external gateways
    5. Persists full audit trail across all layers
    """
    try:
        event_payload = request.event_data if request.event_data is not None else request.event_id
        if not event_payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'event_id' or 'event_data' must be provided in request payload."
            )

        # 1. Decision Engine Phase
        decision_result: DecisionResult = await decision_engine_service.decide_recovery_action(
            event_data=event_payload,
            policy_overrides=request.policy_overrides,
            db=db,
        )

        dec_dict = decision_result.to_dict()
        event_id = dec_dict["event_id"]
        customer_id = dec_dict["customer_id"]
        selected_action = dec_dict["selected_action"]
        risk_score = dec_dict["risk_score"]
        priority = dec_dict.get("priority")
        expected_rec_val = dec_dict["expected_recovery_value"]
        decision_score = dec_dict.get("decision_score")

        # 2. Guardrail Engine Phase (Live Validation)
        guardrail_result: GuardrailValidationResult = guardrail_engine_service.validate(
            decision=dec_dict,
            context=request.event_data,
            current_purchase_status=request.current_purchase_status,
            policy_overrides=request.policy_overrides,
            db=db,
            idempotency_key=idempotency_key,
        )

        # 3. Execution Phase
        is_approved = (
            guardrail_result.status == GuardrailStatus.APPROVED
            or str(getattr(guardrail_result.status, "value", guardrail_result.status)) == "APPROVED"
        )
        if is_approved:
            execution_res: ExecutionResult = await execution_engine_service.execute_decision(

                decision_id=decision_result.decision_id,
                event_id=event_id,
                event_data=request.event_data,
                current_purchase_status=request.current_purchase_status,
                policy_overrides=request.policy_overrides,
                idempotency_key=idempotency_key,
                db=db,
            )

            is_link_created = bool(execution_res.payment_link_id is not None)

            return RecoveryRunResponse(
                event_id=event_id,
                customer_id=customer_id,
                risk_score=risk_score,
                priority=priority,
                selected_action=selected_action,
                decision_score=decision_score,
                guardrail_status="APPROVED",
                execution_status=execution_res.status,
                expected_recovery_value=expected_rec_val,
                payment_link_created=is_link_created,
                payment_link_id=execution_res.payment_link_id,
                payment_url=execution_res.payment_url,
                execution_id=execution_res.execution_id,
                reason=execution_res.reason or "Recovery action executed successfully.",
                blocked_reasons=[],
            )
        else:
            # Blocked or Review Required path (No execution attempted)
            return RecoveryRunResponse(
                event_id=event_id,
                customer_id=customer_id,
                risk_score=risk_score,
                priority=priority,
                selected_action=selected_action,
                decision_score=decision_score,
                guardrail_status=guardrail_result.status.value,
                execution_status="REJECTED",
                expected_recovery_value=expected_rec_val,
                payment_link_created=False,
                payment_link_id=None,
                payment_url=None,
                execution_id=None,
                reason="; ".join(guardrail_result.blocked_reasons) if guardrail_result.blocked_reasons else "Guardrails prevented execution.",
                blocked_reasons=guardrail_result.blocked_reasons,
            )

    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recovery Pipeline failed: {str(e)}"
        )
