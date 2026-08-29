"""
Database Model and Persistence Helpers for RecoverAI AI Decisions (Day 4)
Stores structured diagnosis recommendations, probabilities, and audit logs.
"""

import sys
import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, JSON
from sqlalchemy.orm import Session

# Ensure database and root paths are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from database.database import Base


class AIDecision(Base):
    """
    Persisted AI Diagnosis & Recovery Recommendation decision record.
    Acts as an immutable audit trail of what the AI recommended for each event.
    """
    __tablename__ = "ai_decisions"

    decision_id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), index=True, nullable=False)
    customer_id = Column(String(64), index=True, nullable=False)
    diagnosis = Column(String(64), nullable=False)
    recovery_probability = Column(Float, nullable=False)
    expected_recovery_value = Column(Float, nullable=False, default=0.0)
    revenue_at_risk = Column(Float, nullable=False, default=0.0)
    recommended_action = Column(String(64), nullable=False)
    priority = Column(String(32), nullable=False)
    recommendation_confidence = Column(Float, nullable=False)
    reason_codes = Column(Text, nullable=True)  # JSON-encoded list of reason codes
    explanation = Column(Text, nullable=False)
    suggested_message = Column(Text, nullable=False)
    model_name = Column(String(64), nullable=True)
    source = Column(String(32), nullable=False, default="ai")  # "ai" or "fallback"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model record to dictionary."""
        try:
            reasons = json.loads(self.reason_codes) if self.reason_codes else []
        except Exception:
            reasons = [self.reason_codes] if self.reason_codes else []

        return {
            "decision_id": self.decision_id,
            "event_id": self.event_id,
            "customer_id": self.customer_id,
            "diagnosis": self.diagnosis,
            "recovery_probability": self.recovery_probability,
            "expected_recovery_value": self.expected_recovery_value,
            "revenue_at_risk": self.revenue_at_risk,
            "recommended_action": self.recommended_action,
            "priority": self.priority,
            "recommendation_confidence": self.recommendation_confidence,
            "reason_codes": reasons,
            "explanation": self.explanation,
            "suggested_message": self.suggested_message,
            "model_name": self.model_name,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AIDecision {self.decision_id} (Event: {self.event_id}, "
            f"Action: {self.recommended_action}, Prob: {self.recovery_probability:.2f})>"
        )


def save_ai_decision(db: Session, decision_data: Dict[str, Any]) -> AIDecision:
    """
    Saves or updates an AI decision in the database.
    """
    event_id = str(decision_data["event_id"])
    customer_id = str(decision_data.get("customer_id", "cust_unknown"))

    decision_id = str(decision_data.get("decision_id") or f"dec_{uuid.uuid4().hex[:12]}")

    reasons = decision_data.get("reason_codes", [])
    if isinstance(reasons, list):
        reason_codes_json = json.dumps(reasons)
    else:
        reason_codes_json = json.dumps([str(reasons)])

    # Check if record already exists by decision_id
    existing = db.query(AIDecision).filter(AIDecision.decision_id == decision_id).first()
    if existing:
        existing.event_id = event_id
        existing.customer_id = customer_id
        existing.diagnosis = str(decision_data["diagnosis"])
        existing.recovery_probability = float(decision_data["recovery_probability"])
        existing.expected_recovery_value = float(decision_data.get("expected_recovery_value", 0.0))
        existing.revenue_at_risk = float(decision_data.get("revenue_at_risk", 0.0))
        existing.recommended_action = str(decision_data["recommended_action"])
        existing.priority = str(decision_data["priority"])
        existing.recommendation_confidence = float(decision_data["recommendation_confidence"])
        existing.reason_codes = reason_codes_json
        existing.explanation = str(decision_data["explanation"])
        existing.suggested_message = str(decision_data["suggested_message"])
        existing.model_name = decision_data.get("model_name", "gpt-4o-mini")
        existing.source = decision_data.get("source", "ai")
        db.commit()
        db.refresh(existing)
        return existing

    record = AIDecision(
        decision_id=decision_id,
        event_id=event_id,
        customer_id=customer_id,
        diagnosis=str(decision_data["diagnosis"]),
        recovery_probability=float(decision_data["recovery_probability"]),
        expected_recovery_value=float(decision_data.get("expected_recovery_value", 0.0)),
        revenue_at_risk=float(decision_data.get("revenue_at_risk", 0.0)),
        recommended_action=str(decision_data["recommended_action"]),
        priority=str(decision_data["priority"]),
        recommendation_confidence=float(decision_data["recommendation_confidence"]),
        reason_codes=reason_codes_json,
        explanation=str(decision_data["explanation"]),
        suggested_message=str(decision_data["suggested_message"]),
        model_name=decision_data.get("model_name", "gpt-4o-mini"),
        source=decision_data.get("source", "ai"),
        created_at=datetime.utcnow(),
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_decision_by_event_id(db: Session, event_id: str) -> Optional[AIDecision]:
    """
    Retrieves the most recent decision record for a given event_id.
    """
    return (
        db.query(AIDecision)
        .filter(AIDecision.event_id == event_id)
        .order_by(AIDecision.created_at.desc())
        .first()
    )


def format_ai_decision_summary(decision: AIDecision) -> str:
    """
    Formats a human-readable audit trail summary block for UI / reports.
    """
    d = decision.to_dict()
    reasons_str = ", ".join(d["reason_codes"]) if d["reason_codes"] else "None"
    summary = (
        f"======================================================================\n"
        f" RecoverAI Decision Audit Trail: {d['decision_id']}\n"
        f"----------------------------------------------------------------------\n"
        f" Event ID                  : {d['event_id']}\n"
        f" Customer ID               : {d['customer_id']}\n"
        f" Root Cause Diagnosis      : {d['diagnosis']}\n"
        f" Recommended Action        : {d['recommended_action']}\n"
        f" Priority Tier             : {d['priority']}\n"
        f" Recovery Probability (AI) : {d['recovery_probability'] * 100:.1f}%\n"
        f" Recommendation Confidence : {d['recommendation_confidence'] * 100:.1f}%\n"
        f" Revenue at Risk           : INR {d['revenue_at_risk']:,.2f}\n"
        f" Expected Recovery Value   : INR {d['expected_recovery_value']:,.2f}\n"
        f" Decision Source           : {d['source'].upper()} ({d['model_name'] or 'deterministic'})\n"
        f" Reason Codes              : {reasons_str}\n"
        f" Explanation               : {d['explanation']}\n"
        f" Suggested Message         : \"{d['suggested_message']}\"\n"
        f"======================================================================"
    )
    return summary


__all__ = [
    "AIDecision",
    "save_ai_decision",
    "get_decision_by_event_id",
    "format_ai_decision_summary",
]
