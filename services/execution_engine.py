"""
RecoverAI Recovery Execution Engine (Day 7)
Orchestrates verified execution of approved recovery decisions via Razorpay Test Mode or internal channels.
Enforces real-time re-validation, idempotency, state transitions, and audit trails.
"""

import os
import sys
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# Ensure root & backend paths are on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ai.schemas import (
    RecoveryAction,
    GuardrailStatus,
    ExecutionState,
    AIDecisionContext,
)
from backend.utils.currency import rupees_to_paise, paise_to_rupees
from backend.services.razorpay_service import razorpay_service, RazorpayService
from backend.services.guardrail_engine import guardrail_engine_service, GuardrailEngine
from backend.services.decision_engine import decision_engine_service, DecisionResult
from database.decision_models import RecoveryDecision, get_recovery_decision_by_event_id
from database.execution_models import (
    RecoveryExecution,
    save_execution_record,
    get_execution_by_id,
    get_execution_by_decision_id,
    get_execution_by_idempotency_key,
    get_execution_by_payment_link_id,
)
from database.recovery_models import RecoveryRecord, save_recovery_record
from database.audit_models import GuardrailAuditLog, save_guardrail_audit_log

logger = logging.getLogger(__name__)


class ExecutionResult(BaseModel):
    """
    Structured execution outcome returned by ExecutionEngine.
    """
    execution_id: Optional[str] = None
    decision_id: str
    event_id: str
    customer_id: str
    action: str
    status: str = Field(..., description="'CREATED', 'SUCCEEDED', 'REJECTED', 'FAILED', 'EXPIRED'")
    execution_state: str = Field(..., description="State machine phase")
    amount: float = Field(default=0.0)
    currency: str = Field(default="INR")
    provider: str = Field(default="razorpay")
    payment_link_id: Optional[str] = None
    payment_url: Optional[str] = None
    reason: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "decision_id": self.decision_id,
            "event_id": self.event_id,
            "customer_id": self.customer_id,
            "action": self.action,
            "status": self.status,
            "execution_state": self.execution_state,
            "amount": round(self.amount, 2),
            "currency": self.currency,
            "provider": self.provider,
            "payment_link_id": self.payment_link_id,
            "payment_url": self.payment_url,
            "reason": self.reason,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at,
        }


class ExecutionEngine:
    """
    RecoverAI Execution Engine.
    Strict gatekeeper connecting approved recovery decisions to Razorpay Test Mode or internal channels.
    """

    def __init__(self, razorpay_client_service: Optional[RazorpayService] = None):
        self.razorpay = razorpay_client_service or razorpay_service
        self.guardrails = guardrail_engine_service

    async def execute_decision(
        self,
        decision_id: Optional[str] = None,
        event_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        current_purchase_status: Optional[str] = None,
        policy_overrides: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Executes a recovery decision with multi-layer verification:
        1. Checks Idempotency: Returns existing active execution if already created
        2. Resolves Decision: Retrieves from DB or executes decision engine
        3. Pre-execution Re-Verification: Independently re-runs Guardrail Engine on current live state
        4. Rejects if not APPROVED (even if caller bypassed normal guardrails)
        5. Action Routing:
           - PAYMENT_LINK -> Calls Razorpay Service (Test Mode) with rupees_to_paise conversion
           - NON-PAYMENT (Reminders/Follow-ups) -> Creates internal dispatch event
        6. Persists Execution & Audit Record in DB
        """
        # 1. Resolve Decision Record
        decision_dict: Optional[Dict[str, Any]] = None

        if decision_id and db:
            db_dec = db.query(RecoveryDecision).filter(RecoveryDecision.decision_id == decision_id).first()
            if db_dec:
                decision_dict = db_dec.to_dict()

        if decision_dict is None and event_id and db:
            db_dec = get_recovery_decision_by_event_id(db, event_id)
            if db_dec:
                decision_dict = db_dec.to_dict()

        if decision_dict is None and (event_id or event_data):
            # Compute fresh decision via Decision Engine
            payload = event_data if event_data is not None else event_id
            dec_result = await decision_engine_service.decide_recovery_action(
                event_data=payload,
                policy_overrides=policy_overrides,
                db=db,
            )
            decision_dict = dec_result.to_dict()

        if decision_dict is None:
            return ExecutionResult(
                execution_id=None,
                decision_id=decision_id or "unknown",
                event_id=event_id or "unknown",
                customer_id="unknown",
                action="UNKNOWN",
                status="REJECTED",
                execution_state=ExecutionState.BLOCKED.value,
                reason="Decision record not found or could not be generated.",
            )

        dec_id = str(decision_dict["decision_id"])
        evt_id = str(decision_dict["event_id"])
        cust_id = str(decision_dict.get("customer_id", "cust_unknown"))
        action_str = str(decision_dict.get("selected_action", "NO_ACTION"))
        amount = float(decision_dict.get("cart_value") or decision_dict.get("expected_recovery_value") or 0.0)
        
        try:
            action = RecoveryAction(action_str)
        except Exception:
            action = RecoveryAction.NO_ACTION

        # 2. Idempotency Check
        computed_idempotency_key = idempotency_key or f"exec:{dec_id}:{action.value}"
        if db:
            existing_exec = get_execution_by_idempotency_key(db, computed_idempotency_key)
            if existing_exec:
                logger.info(f"Existing execution found for idempotency key '{computed_idempotency_key}'. Returning record.")
                return ExecutionResult(
                    execution_id=existing_exec.execution_id,
                    decision_id=existing_exec.decision_id,
                    event_id=existing_exec.event_id,
                    customer_id=existing_exec.customer_id,
                    action=existing_exec.action,
                    status=existing_exec.status,
                    execution_state=existing_exec.execution_state,
                    amount=existing_exec.amount,
                    currency=existing_exec.currency,
                    provider=existing_exec.provider,
                    payment_link_id=existing_exec.payment_link_id,
                    payment_url=existing_exec.payment_url,
                    reason="Existing execution record retrieved via idempotency key.",
                    idempotency_key=computed_idempotency_key,
                    created_at=existing_exec.created_at.isoformat() if existing_exec.created_at else None,
                )

        # 3. Pre-execution Re-Verification via Guardrail Engine
        # Strictly re-evaluate NOW — never trust a stale flag from hours ago
        guardrail_result = self.guardrails.validate(
            decision=decision_dict,
            context=event_data,
            current_purchase_status=current_purchase_status,
            policy_overrides=policy_overrides,
            db=db,
        )

        # 4. Reject if not APPROVED
        if guardrail_result.status != GuardrailStatus.APPROVED:
            rejection_reason = (
                f"Decision is not approved for execution: {'; '.join(guardrail_result.blocked_reasons)}"
                if guardrail_result.blocked_reasons
                else "Decision is not approved for execution (Guardrails BLOCKED/REVIEW_REQUIRED)."
            )
            logger.warning(f"Execution rejected for {dec_id}: {rejection_reason}")
            
            # Log audit trail for blocked execution attempt
            if db:
                try:
                    save_guardrail_audit_log(db, {
                        "decision_id": dec_id,
                        "event_id": evt_id,
                        "customer_id": cust_id,
                        "action": action.value,
                        "status": "BLOCKED",
                        "execution_state": ExecutionState.BLOCKED.value,
                        "reason": rejection_reason,
                        "checks": [c.to_dict() for c in guardrail_result.checks],
                        "idempotency_key": computed_idempotency_key,
                    })
                except Exception as e:
                    logger.warning(f"Could not persist rejection audit log: {e}")

            return ExecutionResult(
                execution_id=None,
                decision_id=dec_id,
                event_id=evt_id,
                customer_id=cust_id,
                action=action.value,
                status="REJECTED",
                execution_state=ExecutionState.BLOCKED.value,
                amount=amount,
                reason=rejection_reason,
                idempotency_key=computed_idempotency_key,
            )

        # 5. Execute Approved Action
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        now_dt = datetime.utcnow()

        if action == RecoveryAction.PAYMENT_LINK:
            # Convert INR to integer paise
            amount_paise = rupees_to_paise(amount if amount > 0 else 100.0)
            
            # Customer details
            cust_info = {
                "name": f"Customer {cust_id[-6:]}",
                "email": f"{cust_id}@customer.recoverai.io",
                "phone": "+919876543210",
            }
            
            razorpay_res = self.razorpay.create_payment_link(
                amount_paise=amount_paise,
                currency="INR",
                customer_info=cust_info,
                description=f"RecoverAI Payment Recovery for Event {evt_id}",
                reference_id=f"rec_{evt_id}_{execution_id[:6]}",
                notes={
                    "decision_id": dec_id,
                    "event_id": evt_id,
                    "customer_id": cust_id,
                    "execution_id": execution_id,
                },
            )

            if razorpay_res.get("success"):
                exec_status = "CREATED"
                exec_state = ExecutionState.READY_FOR_EXECUTION.value
                plink_id = razorpay_res.get("payment_link_id")
                plink_url = razorpay_res.get("payment_url")
                err_code = None
                err_msg = None
            else:
                exec_status = "FAILED"
                exec_state = ExecutionState.FAILED.value
                plink_id = None
                plink_url = None
                err_code = razorpay_res.get("error_code", "RAZORPAY_FAILURE")
                err_msg = razorpay_res.get("error_message", "Failed to create payment link.")

            provider = "razorpay"

        elif action in (RecoveryAction.CHECKOUT_REMINDER, RecoveryAction.PERSONALIZED_REMINDER, RecoveryAction.DELAYED_FOLLOW_UP):
            # Non-payment communication action
            exec_status = "CREATED"
            exec_state = ExecutionState.READY_FOR_EXECUTION.value
            plink_id = None
            plink_url = None
            err_code = None
            err_msg = None
            provider = "internal"

        else:
            # NO_ACTION or other
            exec_status = "CREATED"
            exec_state = ExecutionState.SUCCEEDED.value
            plink_id = None
            plink_url = None
            err_code = None
            err_msg = None
            provider = "internal"

        # 6. Persist Execution Record in DB
        exec_payload = {
            "execution_id": execution_id,
            "decision_id": dec_id,
            "event_id": evt_id,
            "customer_id": cust_id,
            "action": action.value,
            "status": exec_status,
            "execution_state": exec_state,
            "amount": amount,
            "currency": "INR",
            "provider": provider,
            "payment_link_id": plink_id,
            "payment_url": plink_url,
            "error_code": err_code,
            "error_message": err_msg,
            "idempotency_key": computed_idempotency_key,
        }

        if db:
            try:
                save_execution_record(db, exec_payload)
                
                # Also log audit event
                save_guardrail_audit_log(db, {
                    "decision_id": dec_id,
                    "event_id": evt_id,
                    "customer_id": cust_id,
                    "action": action.value,
                    "status": "APPROVED",
                    "execution_state": exec_state,
                    "reason": f"Execution dispatched via {provider} ({exec_status}).",
                    "idempotency_key": computed_idempotency_key,
                })
            except Exception as db_err:
                logger.warning(f"Error persisting execution record: {db_err}")

        return ExecutionResult(
            execution_id=execution_id,
            decision_id=dec_id,
            event_id=evt_id,
            customer_id=cust_id,
            action=action.value,
            status=exec_status,
            execution_state=exec_state,
            amount=amount,
            currency="INR",
            provider=provider,
            payment_link_id=plink_id,
            payment_url=plink_url,
            error_code=err_code,
            error_message=err_msg,
            idempotency_key=computed_idempotency_key,
            created_at=now_dt.isoformat(),
        )


# Global singleton instance
execution_engine_service = ExecutionEngine()

__all__ = [
    "ExecutionResult",
    "ExecutionEngine",
    "execution_engine_service",
]
