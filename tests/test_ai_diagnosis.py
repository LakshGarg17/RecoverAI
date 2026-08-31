"""
Unit and Integration Tests for RecoverAI AI Diagnosis Agent (Day 4)
Tests structured outputs, schema validation, fallback mechanics, context building, and persistence.
"""

import os
import sys
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

# Ensure root & backend paths are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ai.schemas import (
    DiagnosisCategory,
    RecoveryAction,
    PriorityTier,
    AIDiagnosisResult,
    AIDecisionContext,
    DiagnoseEventResponse,
)
from ai.prompts import SYSTEM_PROMPT, build_diagnosis_user_prompt
from ai.diagnosis import (
    build_ai_decision_context,
    generate_deterministic_fallback,
    ai_diagnosis_agent,
)
from database.database import SessionLocal, init_db
from database.ai_decisions import save_ai_decision, get_decision_by_event_id, format_ai_decision_summary
from backend.app.main import app

client = TestClient(app)


def test_ai_diagnosis_schema_valid():
    """Verify that a well-formed dictionary passes AIDiagnosisResult validation."""
    valid_payload = {
        "diagnosis": "HIGH_PURCHASE_INTENT_ABANDONMENT",
        "recovery_probability": 0.84,
        "recommended_action": "CHECKOUT_REMINDER",
        "priority": "HIGH",
        "recommendation_confidence": 0.92,
        "reason_codes": ["high_cart_value", "strong_engagement", "recent_abandonment"],
        "explanation": "Customer spent 18 minutes exploring catalog and left items in cart.",
        "suggested_message": "Complete your purchase today to secure fast dispatch!",
    }

    result = AIDiagnosisResult.model_validate(valid_payload)
    assert result.diagnosis == DiagnosisCategory.HIGH_PURCHASE_INTENT_ABANDONMENT
    assert result.recovery_probability == 0.84
    assert result.recommended_action == RecoveryAction.CHECKOUT_REMINDER
    assert result.priority == PriorityTier.HIGH
    assert result.recommendation_confidence == 0.92


def test_ai_diagnosis_schema_invalid_recovery_probability():
    """Verify that out-of-bound recovery_probability raises a ValidationError."""
    invalid_payload = {
        "diagnosis": "HIGH_PURCHASE_INTENT_ABANDONMENT",
        "recovery_probability": 1.75,  # Invalid: > 1.0
        "recommended_action": "CHECKOUT_REMINDER",
        "priority": "HIGH",
        "recommendation_confidence": 0.92,
        "reason_codes": ["test"],
        "explanation": "Valid test explanation text.",
        "suggested_message": "Test message.",
    }

    with pytest.raises(ValidationError):
        AIDiagnosisResult.model_validate(invalid_payload)


def test_ai_diagnosis_schema_invalid_action():
    """Verify that an unknown action category is rejected."""
    invalid_payload = {
        "diagnosis": "HIGH_PURCHASE_INTENT_ABANDONMENT",
        "recovery_probability": 0.80,
        "recommended_action": "SEND_SPAM_CALLS",  # Not in RecoveryAction enum
        "priority": "HIGH",
        "recommendation_confidence": 0.90,
        "reason_codes": ["test"],
        "explanation": "Valid test explanation text.",
        "suggested_message": "Test message.",
    }

    with pytest.raises(ValidationError):
        AIDiagnosisResult.model_validate(invalid_payload)


def test_ai_diagnosis_schema_missing_field():
    """Verify that a missing required field (explanation) raises ValidationError."""
    invalid_payload = {
        "diagnosis": "HIGH_PURCHASE_INTENT_ABANDONMENT",
        "recovery_probability": 0.80,
        "recommended_action": "CHECKOUT_REMINDER",
        "priority": "HIGH",
        "recommendation_confidence": 0.90,
        # Missing 'explanation'
        "suggested_message": "Test message.",
    }

    with pytest.raises(ValidationError):
        AIDiagnosisResult.model_validate(invalid_payload)


def test_build_ai_decision_context():
    """Verify context builder seamlessly integrates telemetry, history, and Day 3 risk scores."""
    mock_event = {
        "event_id": "evt_000666",
        "customer_id": "cust_05529",
        "session_id": "sess_000666",
        "cart_value": 7735.08,
        "session_duration": 1350,
        "pages_viewed": 22,
        "payment_method": "CARD",
        "purchase_status": "abandoned",
        "purchase_history": 3,
        "customer_lifetime_value": 5400.0,
    }

    ctx = build_ai_decision_context(mock_event)
    assert ctx.event_id == "evt_000666"
    assert ctx.customer_id == "cust_05529"
    assert ctx.cart_value == 7735.08
    assert ctx.risk_score >= 80.0
    assert ctx.priority == "CRITICAL"
    assert ctx.revenue_at_risk == 7735.08
    assert ctx.expected_recoverable_revenue > 0.0


def test_deterministic_fallback_scenarios():
    """Verify deterministic fallback logic across test archetypes."""
    # Case A: VIP repeat buyer (CRITICAL priority, prior purchases)
    ctx_vip = AIDecisionContext(
        event_id="evt_vip",
        customer_id="cust_vip",
        cart_value=8500.0,
        session_duration=1400,
        pages_viewed=20,
        previous_purchases=4,
        customer_lifetime_value=12000.0,
        risk_score=92.0,
        priority="CRITICAL",
        purchase_intent_score=88.0,
        revenue_at_risk=8500.0,
        expected_recoverable_revenue=7480.0,
    )
    res_vip = generate_deterministic_fallback(ctx_vip)
    assert res_vip.diagnosis == DiagnosisCategory.REPEAT_CUSTOMER_ABANDONMENT
    assert res_vip.recommended_action == RecoveryAction.PERSONALIZED_REMINDER
    assert res_vip.priority == PriorityTier.CRITICAL
    assert res_vip.recovery_probability >= 0.75

    # Case B: High engagement abandoned cart (HIGH priority)
    ctx_high = AIDecisionContext(
        event_id="evt_high",
        customer_id="cust_high",
        cart_value=3200.0,
        session_duration=1100,
        pages_viewed=17,
        previous_purchases=1,
        customer_lifetime_value=2400.0,
        risk_score=72.0,
        priority="HIGH",
        purchase_intent_score=75.0,
        revenue_at_risk=3200.0,
        expected_recoverable_revenue=2400.0,
    )
    res_high = generate_deterministic_fallback(ctx_high)
    assert res_high.diagnosis == DiagnosisCategory.HIGH_PURCHASE_INTENT_ABANDONMENT
    assert res_high.recommended_action == RecoveryAction.CHECKOUT_REMINDER
    assert res_high.priority == PriorityTier.HIGH

    # Case C: Low intent / browsing (LOW priority)
    ctx_low = AIDecisionContext(
        event_id="evt_low",
        customer_id="cust_low",
        cart_value=0.0,
        session_duration=60,
        pages_viewed=2,
        purchase_status="browsing",
        previous_purchases=0,
        customer_lifetime_value=0.0,
        risk_score=15.0,
        priority="LOW",
        purchase_intent_score=10.0,
        revenue_at_risk=0.0,
        expected_recoverable_revenue=0.0,
    )
    res_low = generate_deterministic_fallback(ctx_low)
    assert res_low.diagnosis == DiagnosisCategory.LOW_INTENT_ABANDONMENT
    assert res_low.recommended_action == RecoveryAction.NO_ACTION
    assert res_low.priority == PriorityTier.LOW

    # Case D: New customer with high-value cart (CRITICAL, 0 prior purchases)
    ctx_new_high = AIDecisionContext(
        event_id="evt_new_high",
        customer_id="cust_new",
        cart_value=6000.0,
        session_duration=1200,
        pages_viewed=18,
        previous_purchases=0,
        customer_lifetime_value=0.0,
        risk_score=82.0,
        priority="CRITICAL",
        purchase_intent_score=80.0,
        revenue_at_risk=6000.0,
        expected_recoverable_revenue=4800.0,
    )
    res_new_high = generate_deterministic_fallback(ctx_new_high)
    assert res_new_high.diagnosis == DiagnosisCategory.HIGH_VALUE_ABANDONMENT
    assert res_new_high.recommended_action == RecoveryAction.PAYMENT_LINK
    assert res_new_high.recommendation_confidence <= 0.88


@pytest.mark.asyncio
async def test_agent_diagnose_event_forced_fallback():
    """Verify AIDiagnosisAgent returns well-structured fallback when forced."""
    mock_event = {
        "event_id": "evt_test_fallback",
        "customer_id": "cust_test",
        "cart_value": 4500.0,
        "session_duration": 1200,
        "pages_viewed": 16,
        "payment_method": "UPI",
        "purchase_status": "abandoned",
        "purchase_history": 2,
        "customer_lifetime_value": 3800.0,
    }

    response = await ai_diagnosis_agent.diagnose_event(mock_event, force_fallback=True)
    assert isinstance(response, DiagnoseEventResponse)
    assert response.event_id == "evt_test_fallback"
    assert response.source == "fallback"
    assert 0.0 <= response.recovery_probability <= 1.0
    assert response.expected_recovery_value == round(response.revenue_at_risk * response.recovery_probability, 2)
    assert response.recommended_action in RecoveryAction


def test_ai_decision_database_persistence():
    """Verify decision persistence in SQLite and audit trail summary formatter."""
    init_db()
    db = SessionLocal()
    try:
        import uuid
        test_id = f"dec_test_{uuid.uuid4().hex[:8]}"
        sample_decision = {
            "decision_id": test_id,
            "event_id": "evt_000666",
            "customer_id": "cust_05529",
            "diagnosis": "REPEAT_CUSTOMER_ABANDONMENT",
            "recovery_probability": 0.86,
            "expected_recovery_value": 6652.17,
            "revenue_at_risk": 7735.08,
            "recommended_action": "PERSONALIZED_REMINDER",
            "priority": "CRITICAL",
            "recommendation_confidence": 0.94,
            "reason_codes": ["vip_repeat", "high_clv"],
            "explanation": "VIP customer with 3 prior orders abandoned checkout.",
            "suggested_message": "Hi, your cart is waiting with 1-click checkout!",
            "model_name": "gpt-4o-mini",
            "source": "ai",
        }

        record = save_ai_decision(db, sample_decision)
        assert record.decision_id == test_id

        fetched = get_decision_by_event_id(db, "evt_000666")
        assert fetched is not None
        assert fetched.diagnosis == "REPEAT_CUSTOMER_ABANDONMENT"
        assert fetched.expected_recovery_value == 6652.17

        summary_text = format_ai_decision_summary(fetched)
        assert "evt_000666" in summary_text
        assert "REPEAT_CUSTOMER_ABANDONMENT" in summary_text
        assert "PERSONALIZED_REMINDER" in summary_text
    finally:
        db.close()


def test_api_diagnose_endpoint():
    """Verify POST /api/v1/ai/diagnose and /api/ai/diagnose endpoints."""
    payload = {
        "event_data": {
            "event_id": "evt_api_test_01",
            "customer_id": "cust_api_test",
            "cart_value": 5200.0,
            "session_duration": 1300,
            "pages_viewed": 19,
            "payment_method": "CARD",
            "purchase_status": "abandoned",
            "purchase_history": 2,
            "customer_lifetime_value": 4100.0,
        }
    }

    # Test Versioned Route
    res_v1 = client.post("/api/v1/ai/diagnose", json=payload)
    assert res_v1.status_code == 200
    data_v1 = res_v1.json()
    assert data_v1["event_id"] == "evt_api_test_01"
    assert "diagnosis" in data_v1
    assert "recommended_action" in data_v1
    assert "expected_recovery_value" in data_v1

    # Test Direct Top-Level Route Alias
    res_alias = client.post("/api/ai/diagnose", json=payload)
    assert res_alias.status_code == 200
    data_alias = res_alias.json()
    assert data_alias["event_id"] == "evt_api_test_01"
