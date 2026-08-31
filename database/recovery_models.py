"""
Database Model and Persistence for Recovery Records & Outcomes (Day 7)
Tracks recovered revenue, payment IDs, and reconciliation states.
"""

import sys
import os
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


class RecoveryRecord(Base):
    """
    Persisted recovery outcome record representing successfully captured or pending recoveries.
    Distinguishes potential revenue at risk from confirmed recovered revenue.
    """
    __tablename__ = "recovery_records"

    recovery_id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), index=True, nullable=False)
    customer_id = Column(String(64), index=True, nullable=False)
    execution_id = Column(String(64), index=True, nullable=False)
    action = Column(String(64), nullable=False)
    status = Column(String(32), index=True, nullable=False, default="INITIATED")  # INITIATED, PENDING, RECOVERED, FAILED, EXPIRED
    
    # Financial reconciliation
    original_amount = Column(Float, nullable=False, default=0.0)
    attempted_amount = Column(Float, nullable=False, default=0.0)
    recovered_amount = Column(Float, nullable=False, default=0.0)
    
    # Gateway payment references
    payment_id = Column(String(128), index=True, nullable=True)
    provider_reference = Column(String(128), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    recovered_at = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "event_id": self.event_id,
            "customer_id": self.customer_id,
            "execution_id": self.execution_id,
            "action": self.action,
            "status": self.status,
            "original_amount": round(self.original_amount, 2),
            "attempted_amount": round(self.attempted_amount, 2),
            "recovered_amount": round(self.recovered_amount, 2),
            "payment_id": self.payment_id,
            "provider_reference": self.provider_reference,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "recovered_at": self.recovered_at.isoformat() if self.recovered_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<RecoveryRecord {self.recovery_id} (Event: {self.event_id}, "
            f"Status: {self.status}, Recovered: ₹{self.recovered_amount:.2f}, Payment: {self.payment_id})>"
        )


def save_recovery_record(db: Session, recovery_data: Dict[str, Any]) -> RecoveryRecord:
    """
    Saves or updates a recovery record in the database.
    """
    recovery_id = str(recovery_data.get("recovery_id") or f"rec_{uuid.uuid4().hex[:12]}")
    event_id = str(recovery_data["event_id"])
    customer_id = str(recovery_data.get("customer_id", "cust_unknown"))
    execution_id = str(recovery_data.get("execution_id", "exec_unknown"))

    existing = db.query(RecoveryRecord).filter(RecoveryRecord.recovery_id == recovery_id).first()
    if existing:
        existing.status = str(recovery_data.get("status", existing.status))
        existing.recovered_amount = float(recovery_data.get("recovered_amount", existing.recovered_amount))
        existing.payment_id = recovery_data.get("payment_id", existing.payment_id)
        existing.provider_reference = recovery_data.get("provider_reference", existing.provider_reference)
        if recovery_data.get("recovered_at"):
            existing.recovered_at = recovery_data["recovered_at"]
        db.commit()
        db.refresh(existing)
        return existing

    record = RecoveryRecord(
        recovery_id=recovery_id,
        event_id=event_id,
        customer_id=customer_id,
        execution_id=execution_id,
        action=str(recovery_data.get("action", "NO_ACTION")),
        status=str(recovery_data.get("status", "INITIATED")),
        original_amount=float(recovery_data.get("original_amount", 0.0)),
        attempted_amount=float(recovery_data.get("attempted_amount", 0.0)),
        recovered_amount=float(recovery_data.get("recovered_amount", 0.0)),
        payment_id=recovery_data.get("payment_id"),
        provider_reference=recovery_data.get("provider_reference"),
        created_at=datetime.utcnow(),
        recovered_at=recovery_data.get("recovered_at"),
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_recovery_by_id(db: Session, recovery_id: str) -> Optional[RecoveryRecord]:
    """Retrieve recovery record by recovery_id."""
    return db.query(RecoveryRecord).filter(RecoveryRecord.recovery_id == recovery_id).first()


def get_recovery_by_execution_id(db: Session, execution_id: str) -> Optional[RecoveryRecord]:
    """Retrieve recovery record by execution_id."""
    return db.query(RecoveryRecord).filter(RecoveryRecord.execution_id == execution_id).first()


def get_recovery_by_event_id(db: Session, event_id: str) -> Optional[RecoveryRecord]:
    """Retrieve the latest recovery record for an event."""
    return (
        db.query(RecoveryRecord)
        .filter(RecoveryRecord.event_id == event_id)
        .order_by(RecoveryRecord.created_at.desc())
        .first()
    )


__all__ = [
    "RecoveryRecord",
    "save_recovery_record",
    "get_recovery_by_id",
    "get_recovery_by_execution_id",
    "get_recovery_by_event_id",
]
