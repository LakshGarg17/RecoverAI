"""
Execution API Endpoints (Day 7)
Exposes POST /api/execution/run to execute approved recovery actions via Razorpay Test Mode or internal channels.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Header, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.db import get_db
from backend.services.execution_engine import execution_engine_service, ExecutionResult
from database.execution_models import get_execution_by_id, get_execution_by_decision_id

router = APIRouter()


class ExecutionRunRequest(BaseModel):
    """Payload for executing a recovery decision."""
    decision_id: Optional[str] = Field(None, description="ID of the recovery decision to execute.")
    event_id: Optional[str] = Field(None, description="Event ID if executing without prior decision ID.")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Optional raw or processed event telemetry.")
    current_purchase_status: Optional[str] = Field(None, description="Live purchase status for real-time validation.")
    policy_overrides: Optional[Dict[str, Any]] = Field(None, description="Optional merchant policy overrides.")


class ExecutionRunResponse(BaseModel):
    """Standardized response from POST /api/execution/run."""
    execution_id: Optional[str] = None
    decision_id: str
    event_id: str
    customer_id: str
    action: str
    status: str
    execution_state: str
    amount: float
    currency: str = "INR"
    provider: str = "razorpay"
    payment_link_id: Optional[str] = None
    payment_url: Optional[str] = None
    reason: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: Optional[str] = None


@router.post(
    "/run",
    response_model=ExecutionRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Approved Recovery Action (Day 7 Execution Engine)",
    description="Validates approval status in real-time and dispatches payment recovery via Razorpay Test Mode or internal communication."
)
async def run_execution_endpoint(
    request: ExecutionRunRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    """
    Executes a recovery decision:
    1. Re-evaluates guardrails live on current state (fail-closed)
    2. Rejects if not APPROVED (even if called directly)
    3. Prevents duplicate execution via idempotency keys
    4. Calls Razorpay Test Mode API for PAYMENT_LINK
    5. Dispatches internal tasks for reminders/follow-ups
    6. Persists execution and audit trail in database
    """
    try:
        if not request.decision_id and not request.event_id and not request.event_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide at least one of 'decision_id', 'event_id', or 'event_data'."
            )

        result: ExecutionResult = await execution_engine_service.execute_decision(
            decision_id=request.decision_id,
            event_id=request.event_id,
            event_data=request.event_data,
            current_purchase_status=request.current_purchase_status,
            policy_overrides=request.policy_overrides,
            idempotency_key=idempotency_key,
            db=db,
        )

        res_dict = result.to_dict()
        return ExecutionRunResponse(**res_dict)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution Engine failed: {str(e)}"
        )


@router.get(
    "/{execution_id}",
    summary="Get Execution Record by ID",
    description="Retrieves a persisted execution record by unique execution_id."
)
def get_execution_record_endpoint(execution_id: str, db: Session = Depends(get_db)):
    record = get_execution_by_id(db, execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No execution record found for ID '{execution_id}'."
        )
    return record.to_dict()


@router.get(
    "/decision/{decision_id}",
    summary="Get Execution Record by Decision ID",
    description="Retrieves the execution record associated with a given decision_id."
)
def get_decision_execution_endpoint(decision_id: str, db: Session = Depends(get_db)):
    record = get_execution_by_decision_id(db, decision_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No execution record found for decision_id '{decision_id}'."
        )
    return record.to_dict()
