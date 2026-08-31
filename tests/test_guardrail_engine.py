"""
Unit and Integration Tests for RecoverAI Guardrail Engine & Audit System (Day 6)
Tests modular checks, fail-closed mechanics, idempotency, manual review states, and audit persistence.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure root & backend paths are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ai.schemas import (
    RecoveryAction,
    GuardrailStatus,
    ExecutionState,
    CheckStatus,
    AIDecisionContext,
)
from backend.config.recovery_policy import RecoveryPolicy, DEFAULT_RECOVERY_POLICY, get_recovery_policy
from backend.services.guardrail_engine import (
    GuardrailEngine,
    guardrail_engine_service,
    check_purchase_completion,
    check_risk_threshold,
    check_recovery_probability,
    check_expected_recovery_value,
    check_max_attempts,
    check_cooldown_window,
    check_duplicate_action,
    check_action_permission,
    check_transaction_limit,
    check_customer_contact_frequency,
    check_manual_review_conditions,
)
from database.database import SessionLocal, init_db
from database.audit_models import (
    GuardrailAuditLog,
    save_guardrail_audit_log,
    get_audit_log_by_idempotency_key,
    get_audit_logs_by_decision_id,
)
from database.decision_models import save_recovery_decision
from backend.app.main import app

client = TestClient(app)


# Fixture for a valid baseline decision payload
@pytest.fixture
def valid_recovery_decision() -> dict:
    return {
        "decision_id": "dec_test_valid_001",
        "event_id": "evt_test_valid_001",
        "customer_id": "cust_valid_001",
        "selected_action": "PERSONALIZED_REMINDER",
        "decision_score": 88.5,
        "risk_score": 90.0,
        "estimated_recovery_probability": 0.85,
        "expected_recovery_value": 7650.0,
        "cart_value": 9000.0,
        "purchase_status": "abandoned",
        "purchase_intent_score": 85.0,
        "previous_purchases": 3,
        "session_duration": 450,
    }


# ============================================================================
# 1. Modular Check Function Tests
# ============================================================================

def test_check_purchase_completion():
    # Completed -> FAILED
    c_comp = check_purchase_completion("completed")
    assert c_comp.status == CheckStatus.FAILED
    assert "already completed" in c_comp.message.lower()

    # Success boolean -> FAILED
    c_succ = check_purchase_completion("abandoned", purchase_completed=True)
    assert c_succ.status == CheckStatus.FAILED

    # Abandoned -> PASSED
    c_aban = check_purchase_completion("abandoned", purchase_completed=False)
    assert c_aban.status == CheckStatus.PASSED

    # Missing status -> FAILED (Fail-Closed)
    c_none = check_purchase_completion(None, purchase_completed=None)
    assert c_none.status == CheckStatus.FAILED


def test_check_risk_threshold():
    policy = get_recovery_policy({"minimum_risk_score": 60.0})
    
    # Passing score
    assert check_risk_threshold(90.0, policy).status == CheckStatus.PASSED
    
    # Failing score
    c_low = check_risk_threshold(30.0, policy)
    assert c_low.status == CheckStatus.FAILED
    assert "below merchant threshold" in c_low.message.lower()

    # Missing score -> Fail-Closed
    assert check_risk_threshold(None, policy).status == CheckStatus.FAILED


def test_check_recovery_probability():
    policy = get_recovery_policy({"minimum_recovery_probability": 0.40})
    
    assert check_recovery_probability(0.85, policy).status == CheckStatus.PASSED
    
    c_low = check_recovery_probability(0.20, policy)
    assert c_low.status == CheckStatus.FAILED
    assert "below merchant threshold" in c_low.message.lower()


def test_check_max_attempts():
    policy = get_recovery_policy({"max_recovery_attempts": 2})
    
    assert check_max_attempts(0, policy).status == CheckStatus.PASSED
    assert check_max_attempts(1, policy).status == CheckStatus.PASSED
    
    # Equal to max or greater -> FAILED
    c_max = check_max_attempts(2, policy)
    assert c_max.status == CheckStatus.FAILED
    assert "maximum recovery attempts reached" in c_max.message.lower()


def test_check_cooldown_window():
    policy = get_recovery_policy({"cooldown_minutes": 60})
    
    # First attempt (None) -> PASSED
    assert check_cooldown_window(None, policy).status == CheckStatus.PASSED
    
    # 75 min ago -> PASSED
    assert check_cooldown_window(75.0, policy).status == CheckStatus.PASSED
    
    # 15 min ago -> FAILED
    c_cool = check_cooldown_window(15.0, policy)
    assert c_cool.status == CheckStatus.FAILED
    assert "cooldown active" in c_cool.message.lower()


def test_check_action_permission():
    # Permitted
    policy = get_recovery_policy({"allow_payment_link": False})
    
    c_pay = check_action_permission(RecoveryAction.PAYMENT_LINK, policy)
    assert c_pay.status == CheckStatus.FAILED
    assert "disabled by merchant policy" in c_pay.message.lower()

    c_rem = check_action_permission(RecoveryAction.CHECKOUT_REMINDER, policy)
    assert c_rem.status == CheckStatus.PASSED


def test_check_transaction_limit():
    policy = get_recovery_policy({"max_transaction_value": 100000.0})
    
    assert check_transaction_limit(50000.0, policy).status == CheckStatus.PASSED
    
    c_over = check_transaction_limit(150000.0, policy)
    assert c_over.status == CheckStatus.FAILED
    assert "exceeds merchant maximum limit" in c_over.message.lower()


# ============================================================================
# 2. Comprehensive End-to-End Guardrail Scenarios
# ============================================================================

def test_valid_recovery_approved(valid_recovery_decision):
    """
    Scenario: Valid recovery (risk 90, probability 0.85, 0 attempts)
    Expectation: Status APPROVED, State READY_FOR_EXECUTION, 0 checks failed.
    """
    engine = GuardrailEngine()
    result = engine.validate(
        decision=valid_recovery_decision,
        recovery_attempt_count=0,
        minutes_since_last_attempt=None,
    )

    assert result.status == GuardrailStatus.APPROVED
    assert result.execution_state == ExecutionState.READY_FOR_EXECUTION
    assert result.checks_failed == 0
    assert result.checks_passed >= 8


def test_low_risk_blocked(valid_recovery_decision):
    """
    Scenario: Low risk (risk score 30.0, policy requires 60.0)
    Expectation: Status BLOCKED, State BLOCKED.
    """
    valid_recovery_decision["risk_score"] = 30.0
    engine = GuardrailEngine()
    result = engine.validate(decision=valid_recovery_decision)

    assert result.status == GuardrailStatus.BLOCKED
    assert result.execution_state == ExecutionState.BLOCKED
    assert any("risk score" in r.lower() for r in result.blocked_reasons)


def test_too_many_attempts_blocked(valid_recovery_decision):
    """
    Scenario: Attempts == max (attempts = 2, max = 2)
    Expectation: Status BLOCKED.
    """
    engine = GuardrailEngine()
    result = engine.validate(
        decision=valid_recovery_decision,
        recovery_attempt_count=2,
    )

    assert result.status == GuardrailStatus.BLOCKED
    assert any("maximum recovery attempts" in r.lower() for r in result.blocked_reasons)


def test_cooldown_violated_blocked(valid_recovery_decision):
    """
    Scenario: Cooldown violated (last attempt 15 min ago, cooldown 60 min)
    Expectation: Status BLOCKED.
    """
    engine = GuardrailEngine()
    result = engine.validate(
        decision=valid_recovery_decision,
        minutes_since_last_attempt=15.0,
    )

    assert result.status == GuardrailStatus.BLOCKED
    assert any("cooldown" in r.lower() for r in result.blocked_reasons)


def test_payment_link_disabled_policy_blocked(valid_recovery_decision):
    """
    Scenario: Payment link disabled via policy
    Expectation: Status BLOCKED.
    """
    valid_recovery_decision["selected_action"] = "PAYMENT_LINK"
    strict_policy = {"allow_payment_link": False}

    engine = GuardrailEngine()
    result = engine.validate(
        decision=valid_recovery_decision,
        policy_overrides=strict_policy,
    )

    assert result.status == GuardrailStatus.BLOCKED
    assert any("disabled by merchant policy" in r.lower() for r in result.blocked_reasons)


def test_purchase_already_completed_blocked(valid_recovery_decision):
    """
    Scenario: Purchase already completed in real-time
    Expectation: Status BLOCKED ("Purchase already completed").
    """
    engine = GuardrailEngine()
    result = engine.validate(
        decision=valid_recovery_decision,
        current_purchase_status="completed",
    )

    assert result.status == GuardrailStatus.BLOCKED
    assert any("already completed" in r.lower() for r in result.blocked_reasons)


def test_high_value_uncertain_signals_review_required(valid_recovery_decision):
    """
    Scenario: High-value cart (₹75,000 >= ₹50,000 threshold) with uncertain/cold user (0 purchases, intent 30)
    Expectation: Status REVIEW_REQUIRED, State REVIEW_REQUIRED.
    """
    valid_recovery_decision["cart_value"] = 75000.0
    valid_recovery_decision["purchase_intent_score"] = 30.0
    valid_recovery_decision["previous_purchases"] = 0
    valid_recovery_decision["session_duration"] = 250

    engine = GuardrailEngine()
    result = engine.validate(decision=valid_recovery_decision)

    assert result.status == GuardrailStatus.REVIEW_REQUIRED
    assert result.execution_state == ExecutionState.REVIEW_REQUIRED
    assert any("manual compliance review" in r.lower() for r in result.blocked_reasons)


def test_fail_closed_on_missing_critical_status(valid_recovery_decision):
    """
    Scenario: Payment status is completely missing and unverified.
    Expectation: Fail-closed -> BLOCKED, never silent approval.
    """
    valid_recovery_decision["purchase_status"] = None
    engine = GuardrailEngine()
    result = engine.validate(
        decision=valid_recovery_decision,
        current_purchase_status=None,
    )

    assert result.status == GuardrailStatus.BLOCKED
    assert any("unverified" in r.lower() or "unavailable" in r.lower() for r in result.blocked_reasons)


# ============================================================================
# 3. Idempotency & Database Audit Tests
# ============================================================================

def test_idempotency_prevents_duplicate_evaluations(valid_recovery_decision):
    """
    Scenario: Repeated calls with the same idempotency key
    Expectation: Returns the existing persisted audit log rather than creating duplicate entries.
    """
    init_db()
    db = SessionLocal()
    try:
        engine = GuardrailEngine()
        idempotency_key = "idemp_test_event_999_key"

        # First evaluation
        result1 = engine.validate(
            decision=valid_recovery_decision,
            db=db,
            idempotency_key=idempotency_key,
        )

        # Second evaluation with identical key
        result2 = engine.validate(
            decision=valid_recovery_decision,
            db=db,
            idempotency_key=idempotency_key,
        )

        assert result1.decision_id == result2.decision_id
        assert result1.status == result2.status
        assert result2.idempotency_key == idempotency_key

        # Verify only 1 record exists in DB for this idempotency key
        logs = db.query(GuardrailAuditLog).filter(GuardrailAuditLog.idempotency_key == idempotency_key).all()
        assert len(logs) == 1

    finally:
        db.close()


# ============================================================================
# 4. API Endpoint Integration Tests
# ============================================================================

def test_api_guardrails_validate_endpoint_approved():
    """Verify POST /api/guardrails/validate returns APPROVED response format."""
    payload = {
        "event_data": {
            "event_id": "evt_api_guard_001",
            "customer_id": "cust_guard_001",
            "cart_value": 6500.0,
            "currency": "INR",
            "payment_method": "UPI",
            "session_duration": 900,
            "pages_viewed": 6,
            "purchase_status": "abandoned",
            "purchase_history": 2,
            "customer_lifetime_value": 12000.0,
        }
    }

    response = client.post("/api/guardrails/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ("APPROVED", "BLOCKED", "REVIEW_REQUIRED")
    assert "action" in data
    assert "checks_passed" in data
    assert "checks_failed" in data
    assert data["checks_passed"] > 0


def test_api_guardrails_validate_endpoint_blocked_completed_cart():
    """Verify POST /api/guardrails/validate returns BLOCKED when cart already completed."""
    payload = {
        "event_data": {
            "event_id": "evt_api_guard_comp",
            "customer_id": "cust_guard_comp",
            "cart_value": 4500.0,
            "purchase_status": "completed",
        },
        "current_purchase_status": "completed",
    }

    response = client.post("/api/guardrails/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "BLOCKED"
    assert data["checks_failed"] >= 1
    assert any("completed" in r.lower() for r in (data.get("blocked_reasons") or [data.get("reason", "")]))
