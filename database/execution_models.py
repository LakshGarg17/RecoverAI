"""
Database Model and Persistence for Recovery Executions (Day 7)
Records external provider calls (e.g. Razorpay Payment Links) and non-payment action dispatches.
"""

import sys
import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Float, Integer, Text, DateTime
from sqlalchemy.orm import Session

# Ensure root & database paths are on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from database.database import Base


class RecoveryExecution(Base):
    """
    Persisted recovery execution record.
    Tracks every action dispatched (Razorpay payment links, reminders, follow-ups).
    """
    __tablename__ = "recovery_executions"

    execution_id = Column(String(64), primary_key=True, index=True)
    decision_id = Column(String(64), index=True, nullable=False)
    event_id = Column(String(64), index=True, nullable=False)
    customer_id = Column(String(64), index=True, nullable=False)
    action = Column(String(64), nullable=False)
    status = Column(String(32), index=True, nullable=False, default="CREATED")  # CREATED, EXECUTING, SUCCEEDED, FAILED, REJECTED, EXPIRED
    execution_state = Column(String(32), nullable=False, default="READY_FOR_EXECUTION")
    
    # Financial details
    amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), nullable=False, default="INR")
    
    # External Provider details (Razorpay Test Mode)
    provider = Column(String(32), nullable=False, default="razorpay")
    provider_reference = Column(String(128), nullable=True)
    payment_link_id = Column(String(128), index=True, nullable=True)
    payment_url = Column(Text, nullable=True)
    
    # Error telemetry
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Idempotency token
    idempotency_key = Column(String(128), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

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
            "provider_reference": self.provider_reference,
            "payment_link_id": self.payment_link_id,
            "payment_url": self.payment_url,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<RecoveryExecution {self.execution_id} (Decision: {self.decision_id}, "
            f"Action: {self.action}, Status: {self.status}, Plink: {self.payment_link_id})>"
        )


def save_execution_record(db: Session, exec_data: Dict[str, Any]) -> RecoveryExecution:
    """
    Saves or updates a recovery execution record.
    """
    execution_id = str(exec_data.get("execution_id") or f"exec_{uuid.uuid4().hex[:12]}")
    decision_id = str(exec_data["decision_id"])
    event_id = str(exec_data["event_id"])
    customer_id = str(exec_data.get("customer_id", "cust_unknown"))

    existing = db.query(RecoveryExecution).filter(RecoveryExecution.execution_id == execution_id).first()
    if existing:
        existing.status = str(exec_data.get("status", existing.status))
        existing.execution_state = str(exec_data.get("execution_state", existing.execution_state))
        existing.provider_reference = exec_data.get("provider_reference", existing.provider_reference)
        existing.payment_link_id = exec_data.get("payment_link_id", existing.payment_link_id)
        existing.payment_url = exec_data.get("payment_url", existing.payment_url)
        existing.error_code = exec_data.get("error_code", existing.error_code)
        existing.error_message = exec_data.get("error_message", existing.error_message)
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    def safe_float(val, default=0.0):
        if val is None:
            return default
        try:
            import math
            f = float(val)
            return default if math.isnan(f) or math.isinf(f) else f
        except Exception:
            return default

    record = RecoveryExecution(
        execution_id=execution_id,
        decision_id=decision_id,
        event_id=event_id,
        customer_id=customer_id,
        action=str(exec_data.get("action", "NO_ACTION")),
        status=str(exec_data.get("status", "CREATED")),
        execution_state=str(exec_data.get("execution_state", "READY_FOR_EXECUTION")),
        amount=safe_float(exec_data.get("amount"), 0.0),
        currency=str(exec_data.get("currency", "INR")),
        provider=str(exec_data.get("provider", "razorpay")),
        provider_reference=exec_data.get("provider_reference"),
        payment_link_id=exec_data.get("payment_link_id"),
        payment_url=exec_data.get("payment_url"),
        error_code=exec_data.get("error_code"),
        error_message=exec_data.get("error_message"),
        idempotency_key=exec_data.get("idempotency_key"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_execution_by_id(db: Session, execution_id: str) -> Optional[RecoveryExecution]:
    """Retrieve execution record by execution_id."""
    return db.query(RecoveryExecution).filter(RecoveryExecution.execution_id == execution_id).first()


def get_execution_by_decision_id(db: Session, decision_id: str) -> Optional[RecoveryExecution]:
    """Retrieve the most recent execution record for a given decision_id."""
    return (
        db.query(RecoveryExecution)
        .filter(RecoveryExecution.decision_id == decision_id)
        .order_by(RecoveryExecution.created_at.desc())
        .first()
    )


def get_execution_by_idempotency_key(db: Session, idempotency_key: str) -> Optional[RecoveryExecution]:
    """Retrieve execution record by idempotency_key."""
    if not idempotency_key:
        return None
    return (
        db.query(RecoveryExecution)
        .filter(RecoveryExecution.idempotency_key == idempotency_key)
        .order_by(RecoveryExecution.created_at.desc())
        .first()
    )


def get_execution_by_payment_link_id(db: Session, payment_link_id: str) -> Optional[RecoveryExecution]:
    """Retrieve execution record by Razorpay payment_link_id."""
    if not payment_link_id:
        return None
    return (
        db.query(RecoveryExecution)
        .filter(RecoveryExecution.payment_link_id == payment_link_id)
        .order_by(RecoveryExecution.created_at.desc())
        .first()
    )


__all__ = [
    "RecoveryExecution",
    "save_execution_record",
    "get_execution_by_id",
    "get_execution_by_decision_id",
    "get_execution_by_idempotency_key",
    "get_execution_by_payment_link_id",
]
