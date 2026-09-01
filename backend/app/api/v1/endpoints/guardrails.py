"""
Guardrail API Endpoints (Day 6)
Exposes POST /api/guardrails/validate to evaluate decisions against risk, policy, and safety guardrails.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Header, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.db import get_db
from ai.schemas import (
    GuardrailStatus,
    ExecutionState,
    GuardrailValidateRequest,
    GuardrailValidateResponse,
)
from backend.services.guardrail_engine import guardrail_engine_service
from backend.services.decision_engine import decision_engine_service
from database.decision_models import get_recovery_decision_by_event_id, RecoveryDecision
from database.audit_models import (
    get_audit_log_by_id,
    get_audit_logs_by_decision_id,
    get_audit_logs_by_customer_id,
)

router = APIRouter()


@router.post(
    "/validate",
    response_model=GuardrailValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate Recovery Decision Through Risk & Policy Guardrails (Day 6)",
    description="Validates a candidate recovery action against 10 modular safety checks before execution."
)
async def validate_recovery_guardrail_endpoint(
    request: GuardrailValidateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    """
    Validates a recovery decision:
    1. Resolves decision via decision_id, event_id, or event_data
    2. Checks idempotency cache to prevent duplicate evaluations
    3. Runs 10 modular safety and policy checks (non-short-circuiting)
    4. Enforces fail-closed behavior on missing or unverified telemetry
    5. Returns APPROVED, BLOCKED, or REVIEW_REQUIRED with execution state
    6. Persists immutable audit record in database
    """
    try:
        decision_obj = None

        # 1. Resolve Decision Object
        if request.decision_id:
            # Query from DB
            db_dec = db.query(RecoveryDecision).filter(RecoveryDecision.decision_id == request.decision_id).first()
            if db_dec:
                decision_obj = db_dec.to_dict()
            else:
                # If not found in DB by decision_id, try event_id if provided
                if request.event_id:
                    db_dec = get_recovery_decision_by_event_id(db, request.event_id)
                    if db_dec:
                        decision_obj = db_dec.to_dict()

        if decision_obj is None and (request.event_id or request.event_data):
            # Compute fresh decision via Decision Engine
            event_payload = request.event_data if request.event_data is not None else request.event_id
            dec_result = await decision_engine_service.decide_recovery_action(
                event_data=event_payload,
                policy_overrides=request.policy_overrides,
                db=db,
            )
            decision_obj = dec_result.to_dict()

        if decision_obj is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not resolve decision. Provide a valid 'decision_id', 'event_id', or 'event_data'."
            )

        # 2. Run Guardrail Engine Validation
        validation_result = guardrail_engine_service.validate(
            decision=decision_obj,
            context=request.event_data,
            current_purchase_status=request.current_purchase_status,
            policy_overrides=request.policy_overrides,
            db=db,
            idempotency_key=idempotency_key,
        )

        res_dict = validation_result.to_dict()

        return GuardrailValidateResponse(
            status=validation_result.status,
            action=validation_result.action.value if hasattr(validation_result.action, "value") else str(validation_result.action),
            execution_state=validation_result.execution_state.value if hasattr(validation_result.execution_state, "value") else str(validation_result.execution_state),
            decision_id=validation_result.decision_id,
            event_id=validation_result.event_id,
            customer_id=validation_result.customer_id,
            checks_passed=validation_result.checks_passed,
            checks_failed=validation_result.checks_failed,
            checks=[c.to_dict() for c in validation_result.checks],
            reasons=validation_result.reasons,
            reason=res_dict.get("reason"),
            blocked_reasons=validation_result.blocked_reasons,
            idempotency_key=validation_result.idempotency_key,
            policy_version=validation_result.policy_version,
        )

    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Guardrail Engine failed (fail-closed): {str(e)}"
        )


@router.get(
    "/policy",
    summary="Get Current Merchant Recovery Policy Configuration",
    description="Returns the active merchant recovery policy thresholds, limits, and guardrail constraints."
)
def get_guardrails_policy_endpoint() -> Dict[str, Any]:
    from backend.config.recovery_policy import get_recovery_policy
    policy = get_recovery_policy()
    return policy.to_dict()


@router.get(
    "/audit/{audit_id}",
    summary="Get Guardrail Audit Record by ID",
    description="Retrieves an immutable guardrail audit record by unique audit_id."
)
def get_audit_record_endpoint(audit_id: str, db: Session = Depends(get_db)):
    record = get_audit_log_by_id(db, audit_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit log found for audit_id '{audit_id}'."
        )
    return record.to_dict()


@router.get(
    "/audit/decision/{decision_id}",
    summary="Get Guardrail Audit Records for Decision",
    description="Retrieves all guardrail audit evaluations for a given decision_id."
)
def get_decision_audit_records_endpoint(decision_id: str, db: Session = Depends(get_db)):
    records = get_audit_logs_by_decision_id(db, decision_id)
    return [r.to_dict() for r in records]

