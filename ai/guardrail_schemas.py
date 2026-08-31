"""
Guardrail Schemas & Execution State Machine (Day 6)
Defines validation status enums, check details, execution states, and audit response contracts.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

from ai.schemas import RecoveryAction


class GuardrailStatus(str, Enum):
    """Controlled decision outcome of the Guardrail Engine."""
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ExecutionState(str, Enum):
    """
    Lifecycle state machine for recovery actions:
    IDENTIFIED -> ANALYZED -> RECOMMENDED -> GUARDRAIL_PENDING -> APPROVED -> READY_FOR_EXECUTION -> EXECUTING -> SUCCEEDED / FAILED
    Branch states: BLOCKED, REVIEW_REQUIRED
    """
    IDENTIFIED = "IDENTIFIED"
    ANALYZED = "ANALYZED"
    RECOMMENDED = "RECOMMENDED"
    GUARDRAIL_PENDING = "GUARDRAIL_PENDING"
    APPROVED = "APPROVED"
    READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class CheckStatus(str, Enum):
    """Status of an individual guardrail check."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    FLAGGED = "FLAGGED"


class GuardrailCheckDetail(BaseModel):
    """Detailed outcome of a single guardrail rule evaluation."""
    name: str = Field(..., description="Machine-readable check identifier (e.g. 'risk_threshold').")
    status: CheckStatus = Field(..., description="PASSED, FAILED, SKIPPED, or FLAGGED.")
    message: str = Field(..., description="Human-readable explanation of check evaluation.")
    value_observed: Optional[Any] = Field(default=None, description="Actual observed metric value.")
    threshold_applied: Optional[Any] = Field(default=None, description="Configured policy limit applied.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "message": self.message,
            "value_observed": self.value_observed,
            "threshold_applied": self.threshold_applied,
        }


class GuardrailValidationResult(BaseModel):
    """
    Comprehensive structured outcome returned by Guardrail Engine.
    Reports the composite status, individual check outcomes, and execution state.
    """
    decision_id: str
    event_id: str
    customer_id: str
    status: GuardrailStatus
    execution_state: ExecutionState
    action: RecoveryAction
    checks_passed: int = Field(default=0, ge=0)
    checks_failed: int = Field(default=0, ge=0)
    checks: List[GuardrailCheckDetail] = Field(default_factory=list)
    blocked_reasons: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    policy_version: str = Field(default="v1.1")
    idempotency_key: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "event_id": self.event_id,
            "customer_id": self.customer_id,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "execution_state": self.execution_state.value if hasattr(self.execution_state, "value") else str(self.execution_state),
            "action": self.action.value if hasattr(self.action, "value") else str(self.action),
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "checks": [c.to_dict() for c in self.checks],
            "blocked_reasons": self.blocked_reasons,
            "reasons": self.reasons if self.reasons else self.blocked_reasons,
            "reason": "; ".join(self.blocked_reasons) if self.blocked_reasons else None,
            "policy_version": self.policy_version,
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GuardrailValidateRequest(BaseModel):
    """Request payload for validating a recovery decision through guardrails."""
    decision_id: Optional[str] = Field(None, description="Existing decision ID to validate.")
    event_id: Optional[str] = Field(None, description="Optional event ID if validating directly.")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Optional raw or processed event dict.")
    policy_overrides: Optional[Dict[str, Any]] = Field(None, description="Optional merchant policy overrides.")
    current_purchase_status: Optional[str] = Field(None, description="Real-time purchase status if known (e.g. 'completed', 'abandoned').")


class GuardrailValidateResponse(BaseModel):
    """Standardized API response for POST /api/guardrails/validate."""
    status: GuardrailStatus
    action: str
    execution_state: Optional[str] = None
    decision_id: Optional[str] = None
    event_id: Optional[str] = None
    customer_id: Optional[str] = None
    checks_passed: int
    checks_failed: int
    checks: Optional[List[Dict[str, Any]]] = None
    reasons: Optional[List[str]] = None
    reason: Optional[str] = None
    blocked_reasons: Optional[List[str]] = None
    idempotency_key: Optional[str] = None
    policy_version: Optional[str] = None


__all__ = [
    "GuardrailStatus",
    "ExecutionState",
    "CheckStatus",
    "GuardrailCheckDetail",
    "GuardrailValidationResult",
    "GuardrailValidateRequest",
    "GuardrailValidateResponse",
]
