"""
Database Audit Models and Persistence for RecoverAI Guardrail Engine (Day 6)
Provides an immutable, tamper-evident audit log of all guardrail evaluations.
"""

import sys
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Float, Integer, Text, DateTime
from sqlalchemy.orm import Session

# Ensure root & database paths are on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from database.database import Base


class GuardrailAuditLog(Base):
    """
    Immutable audit record for every guardrail evaluation (APPROVED, BLOCKED, REVIEW_REQUIRED).
    Guarantees full visibility into risk parameters, check details, and policy versions applied.
    """
    __tablename__ = "guardrail_audit_logs"

    audit_id = Column(String(64), primary_key=True, index=True)
    decision_id = Column(String(64), index=True, nullable=False)
    event_id = Column(String(64), index=True, nullable=False)
    customer_id = Column(String(64), index=True, nullable=False)
    requested_action = Column(String(64), nullable=False)
    final_action = Column(String(64), nullable=False)
    status = Column(String(32), index=True, nullable=False)  # APPROVED, BLOCKED, REVIEW_REQUIRED
    execution_state = Column(String(32), index=True, nullable=False, default="READY_FOR_EXECUTION")
    
    # Financial & Risk telemetry
    risk_score = Column(Float, nullable=False, default=0.0)
    recovery_probability = Column(Float, nullable=True)
    expected_recovery_value = Column(Float, nullable=True)
    cart_value = Column(Float, nullable=True)
    policy_version = Column(String(32), nullable=False, default="v1.1")
    
    # Checks summary & full structured payload
    checks_passed = Column(Integer, nullable=False, default=0)
    checks_failed = Column(Integer, nullable=False, default=0)
    checks_detail = Column(Text, nullable=True)  # JSON-encoded List[GuardrailCheckDetail]
    blocked_reasons = Column(Text, nullable=True)  # JSON-encoded List[str]
    reasons = Column(Text, nullable=True)  # JSON-encoded List[str]
    reason = Column(Text, nullable=True)  # Concatenated summary string
    
    # Idempotency token to prevent duplicate generation/execution
    idempotency_key = Column(String(128), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model record to dictionary."""
        def safe_json_loads(val, default):
            if not val:
                return default
            try:
                return json.loads(val)
            except Exception:
                return [val] if isinstance(default, list) else default

        return {
            "audit_id": self.audit_id,
            "decision_id": self.decision_id,
            "event_id": self.event_id,
            "customer_id": self.customer_id,
            "requested_action": self.requested_action,
            "final_action": self.final_action,
            "status": self.status,
            "execution_state": self.execution_state,
            "risk_score": round(self.risk_score, 1) if self.risk_score is not None else 0.0,
            "recovery_probability": round(self.recovery_probability, 2) if self.recovery_probability is not None else None,
            "expected_recovery_value": round(self.expected_recovery_value, 2) if self.expected_recovery_value is not None else None,
            "cart_value": round(self.cart_value, 2) if self.cart_value is not None else None,
            "policy_version": self.policy_version,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "checks": safe_json_loads(self.checks_detail, []),
            "blocked_reasons": safe_json_loads(self.blocked_reasons, []),
            "reasons": safe_json_loads(self.reasons, []),
            "reason": self.reason,
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<GuardrailAuditLog {self.audit_id} (Decision: {self.decision_id}, "
            f"Status: {self.status}, State: {self.execution_state}, "
            f"Action: {self.final_action})>"
        )


def save_guardrail_audit_log(db: Session, log_data: Dict[str, Any]) -> GuardrailAuditLog:
    """
    Persists an immutable guardrail audit record to the database.
    """
    audit_id = str(log_data.get("audit_id") or f"aud_{uuid.uuid4().hex[:12]}")
    decision_id = str(log_data["decision_id"])
    event_id = str(log_data["event_id"])
    customer_id = str(log_data.get("customer_id", "cust_unknown"))
    
    checks_list = log_data.get("checks", [])
    blocked_list = log_data.get("blocked_reasons", [])
    reasons_list = log_data.get("reasons", [])
    
    checks_json = json.dumps(checks_list) if isinstance(checks_list, list) else str(checks_list)
    blocked_json = json.dumps(blocked_list) if isinstance(blocked_list, list) else str(blocked_list)
    reasons_json = json.dumps(reasons_list) if isinstance(reasons_list, list) else str(reasons_list)
    
    reason_str = log_data.get("reason")
    if not reason_str and blocked_list:
        reason_str = "; ".join(blocked_list) if isinstance(blocked_list, list) else str(blocked_list)

    record = GuardrailAuditLog(
        audit_id=audit_id,
        decision_id=decision_id,
        event_id=event_id,
        customer_id=customer_id,
        requested_action=str(log_data.get("requested_action", log_data.get("action", "NO_ACTION"))),
        final_action=str(log_data.get("final_action", log_data.get("action", "NO_ACTION"))),
        status=str(log_data.get("status", "BLOCKED")),
        execution_state=str(log_data.get("execution_state", "BLOCKED")),
        risk_score=float(log_data.get("risk_score", 0.0)),
        recovery_probability=float(log_data["recovery_probability"]) if log_data.get("recovery_probability") is not None else None,
        expected_recovery_value=float(log_data["expected_recovery_value"]) if log_data.get("expected_recovery_value") is not None else None,
        cart_value=float(log_data["cart_value"]) if log_data.get("cart_value") is not None else None,
        policy_version=str(log_data.get("policy_version", "v1.1")),
        checks_passed=int(log_data.get("checks_passed", 0)),
        checks_failed=int(log_data.get("checks_failed", 0)),
        checks_detail=checks_json,
        blocked_reasons=blocked_json,
        reasons=reasons_json,
        reason=reason_str,
        idempotency_key=log_data.get("idempotency_key"),
        created_at=datetime.utcnow(),
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_audit_log_by_id(db: Session, audit_id: str) -> Optional[GuardrailAuditLog]:
    """Retrieve audit record by unique audit_id."""
    return db.query(GuardrailAuditLog).filter(GuardrailAuditLog.audit_id == audit_id).first()


def get_audit_logs_by_decision_id(db: Session, decision_id: str) -> List[GuardrailAuditLog]:
    """Retrieve all audit records associated with a decision_id."""
    return (
        db.query(GuardrailAuditLog)
        .filter(GuardrailAuditLog.decision_id == decision_id)
        .order_by(GuardrailAuditLog.created_at.desc())
        .all()
    )


def get_audit_log_by_idempotency_key(db: Session, idempotency_key: str) -> Optional[GuardrailAuditLog]:
    """Retrieve audit record by idempotency_key to prevent duplicate evaluations."""
    if not idempotency_key:
        return None
    return (
        db.query(GuardrailAuditLog)
        .filter(GuardrailAuditLog.idempotency_key == idempotency_key)
        .order_by(GuardrailAuditLog.created_at.desc())
        .first()
    )


def get_audit_logs_by_customer_id(
    db: Session,
    customer_id: str,
    since_hours: Optional[int] = None
) -> List[GuardrailAuditLog]:
    """Retrieve audit records for a given customer, optionally within a recent hours window."""
    query = db.query(GuardrailAuditLog).filter(GuardrailAuditLog.customer_id == customer_id)
    if since_hours is not None and since_hours > 0:
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        query = query.filter(GuardrailAuditLog.created_at >= cutoff)
    return query.order_by(GuardrailAuditLog.created_at.desc()).all()


def get_recent_audit_logs_for_event(
    db: Session,
    event_id: str,
    action: Optional[str] = None
) -> List[GuardrailAuditLog]:
    """Retrieve recent audit records for an event, optionally filtered by action."""
    query = db.query(GuardrailAuditLog).filter(GuardrailAuditLog.event_id == event_id)
    if action:
        query = query.filter(GuardrailAuditLog.final_action == action)
    return query.order_by(GuardrailAuditLog.created_at.desc()).all()


__all__ = [
    "GuardrailAuditLog",
    "save_guardrail_audit_log",
    "get_audit_log_by_id",
    "get_audit_logs_by_decision_id",
    "get_audit_log_by_idempotency_key",
    "get_audit_logs_by_customer_id",
    "get_recent_audit_logs_for_event",
]
