"""
Database Model and Persistence for RecoverAI Final Recovery Decisions (Day 5)
Stores the deterministic Decision Engine outcome alongside the original Day 4 AI diagnosis.
"""

import sys
import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Float, Integer, Text, DateTime
from sqlalchemy.orm import Session

# Ensure root & database paths are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from database.database import Base


class RecoveryDecision(Base):
    """
    Persisted Final Recovery Decision record produced by the Decision Engine.
    Maintains complete auditability of candidate scoring, exclusions, policy applied,
    and comparative divergence against the raw AI diagnosis.
    """
    __tablename__ = "recovery_decisions"

    decision_id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), index=True, nullable=False)
    customer_id = Column(String(64), index=True, nullable=False)
    selected_action = Column(String(64), nullable=False)
    decision_score = Column(Float, nullable=False, default=0.0)
    expected_recovery_value = Column(Float, nullable=False, default=0.0)
    estimated_recovery_probability = Column(Float, nullable=False, default=0.0)
    priority = Column(String(32), nullable=False, default="MEDIUM")
    risk_score = Column(Float, nullable=False, default=0.0)
    
    # Audit details & explanations
    reasons = Column(Text, nullable=True)  # JSON-encoded list of reason bullets
    explanation = Column(Text, nullable=False)
    alternative_actions = Column(Text, nullable=True)  # JSON-encoded list of scored alternatives
    excluded_actions = Column(Text, nullable=True)  # JSON-encoded list of excluded actions with reasons
    
    # Raw Day 4 AI Recommendation (preserves AI output for comparison without overwrite)
    ai_recommended_action = Column(String(64), nullable=True)
    ai_recovery_probability = Column(Float, nullable=True)
    ai_diagnosis_category = Column(String(64), nullable=True)
    divergence_reason = Column(Text, nullable=True)
    
    # Applied Merchant Policy snapshot
    policy_applied = Column(Text, nullable=True)  # JSON-encoded policy dict
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

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
            "decision_id": self.decision_id,
            "event_id": self.event_id,
            "customer_id": self.customer_id,
            "selected_action": self.selected_action,
            "decision_score": round(self.decision_score, 1),
            "expected_recovery_value": round(self.expected_recovery_value, 2),
            "estimated_recovery_probability": round(self.estimated_recovery_probability, 2),
            "priority": self.priority,
            "risk_score": round(self.risk_score, 1),
            "reasons": safe_json_loads(self.reasons, []),
            "explanation": self.explanation,
            "alternative_actions": safe_json_loads(self.alternative_actions, []),
            "excluded_actions": safe_json_loads(self.excluded_actions, []),
            "ai_recommendation": {
                "action": self.ai_recommended_action,
                "recovery_probability": self.ai_recovery_probability,
                "diagnosis": self.ai_diagnosis_category,
            } if self.ai_recommended_action else None,
            "divergence_reason": self.divergence_reason,
            "policy_applied": safe_json_loads(self.policy_applied, {}),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<RecoveryDecision {self.decision_id} (Event: {self.event_id}, "
            f"Action: {self.selected_action}, Score: {self.decision_score:.1f}, "
            f"ExpValue: ₹{self.expected_recovery_value:.2f})>"
        )


def save_recovery_decision(db: Session, decision_data: Dict[str, Any]) -> RecoveryDecision:
    """
    Saves or updates a final Recovery Decision in the database.
    """
    event_id = str(decision_data["event_id"])
    customer_id = str(decision_data.get("customer_id", "cust_unknown"))
    decision_id = str(decision_data.get("decision_id") or f"dec_{uuid.uuid4().hex[:12]}")

    reasons_json = json.dumps(decision_data.get("reasons", []))
    alternatives_json = json.dumps(decision_data.get("alternative_actions", []))
    excluded_json = json.dumps(decision_data.get("excluded_actions", []))
    policy_json = json.dumps(decision_data.get("policy_applied", {}))

    ai_rec = decision_data.get("ai_recommendation") or {}
    ai_action = decision_data.get("ai_recommended_action") or ai_rec.get("action")
    ai_prob = decision_data.get("ai_recovery_probability") or ai_rec.get("recovery_probability")
    ai_diag = decision_data.get("ai_diagnosis_category") or ai_rec.get("diagnosis")

    existing = db.query(RecoveryDecision).filter(RecoveryDecision.decision_id == decision_id).first()
    if existing:
        existing.event_id = event_id
        existing.customer_id = customer_id
        existing.selected_action = str(decision_data["selected_action"])
        existing.decision_score = float(decision_data.get("decision_score", 0.0))
        existing.expected_recovery_value = float(decision_data.get("expected_recovery_value", 0.0))
        existing.estimated_recovery_probability = float(decision_data.get("estimated_recovery_probability", 0.0))
        existing.priority = str(decision_data.get("priority", "MEDIUM"))
        existing.risk_score = float(decision_data.get("risk_score", 0.0))
        existing.reasons = reasons_json
        existing.explanation = str(decision_data.get("explanation", ""))
        existing.alternative_actions = alternatives_json
        existing.excluded_actions = excluded_json
        existing.ai_recommended_action = str(ai_action) if ai_action else None
        existing.ai_recovery_probability = float(ai_prob) if ai_prob is not None else None
        existing.ai_diagnosis_category = str(ai_diag) if ai_diag else None
        existing.divergence_reason = decision_data.get("divergence_reason")
        existing.policy_applied = policy_json
        db.commit()
        db.refresh(existing)
        return existing

    record = RecoveryDecision(
        decision_id=decision_id,
        event_id=event_id,
        customer_id=customer_id,
        selected_action=str(decision_data["selected_action"]),
        decision_score=float(decision_data.get("decision_score", 0.0)),
        expected_recovery_value=float(decision_data.get("expected_recovery_value", 0.0)),
        estimated_recovery_probability=float(decision_data.get("estimated_recovery_probability", 0.0)),
        priority=str(decision_data.get("priority", "MEDIUM")),
        risk_score=float(decision_data.get("risk_score", 0.0)),
        reasons=reasons_json,
        explanation=str(decision_data.get("explanation", "")),
        alternative_actions=alternatives_json,
        excluded_actions=excluded_json,
        ai_recommended_action=str(ai_action) if ai_action else None,
        ai_recovery_probability=float(ai_prob) if ai_prob is not None else None,
        ai_diagnosis_category=str(ai_diag) if ai_diag else None,
        divergence_reason=decision_data.get("divergence_reason"),
        policy_applied=policy_json,
        created_at=datetime.utcnow(),
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_recovery_decision_by_event_id(db: Session, event_id: str) -> Optional[RecoveryDecision]:
    """
    Retrieves the most recent recovery decision record for a given event_id.
    """
    return (
        db.query(RecoveryDecision)
        .filter(RecoveryDecision.event_id == event_id)
        .order_by(RecoveryDecision.created_at.desc())
        .first()
    )


__all__ = [
    "RecoveryDecision",
    "save_recovery_decision",
    "get_recovery_decision_by_event_id",
]
