"""
Unit and Integration Tests for RecoverAI Recovery Decision Engine (Day 5)
Tests deterministic scoring, eligibility filtering, policy constraints,
divergence detection, persistence, and API endpoints.
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
    PriorityTier,
    AIDiagnosisResult,
    AIDecisionContext,
    DiagnosisCategory,
)
from backend.config.recovery_policy import RecoveryPolicy, DEFAULT_RECOVERY_POLICY, get_recovery_policy
from backend.services.action_scoring import (
    score_single_action,
    score_all_candidate_actions,
    compute_effective_action_probability,
    ESTIMATED_ACTION_RECOVERY_PROB_NO_ACTION,
    ESTIMATED_ACTION_RECOVERY_PROB_CHECKOUT_REMINDER,
    ESTIMATED_ACTION_RECOVERY_PROB_PERSONALIZED_REMINDER,
    ESTIMATED_ACTION_RECOVERY_PROB_PAYMENT_LINK,
)
from backend.services.decision_engine import (
    RecoveryDecisionEngine,
    decision_engine_service,
    filter_eligible_actions,
    generate_decision_reasons,
    evaluate_ai_divergence,
    DecisionResult,
)
from database.database import SessionLocal, init_db
from database.decision_models import save_recovery_decision, get_recovery_decision_by_event_id
from database.ai_decisions import save_ai_decision, get_decision_by_event_id
from backend.app.main import app

client = TestClient(app)


# Fixture for synthetic contexts
@pytest.fixture
def high_value_high_intent_repeat_context() -> AIDecisionContext:
    return AIDecisionContext(
        event_id="evt_test_high_val_repeat",
        customer_id="cust_vip_001",
        session_id="sess_vip_001",
        cart_value=18000.0,
        currency="INR",
        payment_method="UPI",
        session_duration=1200,
        pages_viewed=8,
        purchase_status="abandoned",
        previous_purchases=4,
        customer_lifetime_value=45000.0,
        average_order_value=11250.0,
        cart_abandonment_rate=0.15,
        total_sessions=6,
        risk_score=92.0,
        priority="CRITICAL",
        purchase_intent_score=90.0,
        revenue_at_risk=18000.0,
        expected_recoverable_revenue=16200.0,
    )


@pytest.fixture
def low_value_low_intent_context() -> AIDecisionContext:
    return AIDecisionContext(
        event_id="evt_test_low_val_cold",
        customer_id="cust_cold_002",
        session_id="sess_cold_002",
        cart_value=45.0,
        currency="INR",
        payment_method="UPI",
        session_duration=25,
        pages_viewed=1,
        purchase_status="abandoned",
        previous_purchases=0,
        customer_lifetime_value=0.0,
        average_order_value=0.0,
        cart_abandonment_rate=0.90,
        total_sessions=1,
        risk_score=15.0,
        priority="LOW",
        purchase_intent_score=12.0,
        revenue_at_risk=45.0,
        expected_recoverable_revenue=4.5,
    )


@pytest.fixture
def high_intent_zero_history_context() -> AIDecisionContext:
    return AIDecisionContext(
        event_id="evt_test_high_intent_new",
        customer_id="cust_new_003",
        session_id="sess_new_003",
        cart_value=3200.0,
        currency="INR",
        payment_method="CARD",
        session_duration=650,
        pages_viewed=6,
        purchase_status="abandoned",
        previous_purchases=0,
        customer_lifetime_value=0.0,
        average_order_value=0.0,
        cart_abandonment_rate=0.0,
        total_sessions=1,
        risk_score=68.0,
        priority="HIGH",
        purchase_intent_score=75.0,
        revenue_at_risk=3200.0,
        expected_recoverable_revenue=2400.0,
    )


# ============================================================================
# 1. Action Scoring Tests
# ============================================================================

def test_action_scoring_named_constants():
    """Verify that per-action starting assumptions are defined as named constants."""
    assert ESTIMATED_ACTION_RECOVERY_PROB_NO_ACTION == 0.05
    assert ESTIMATED_ACTION_RECOVERY_PROB_CHECKOUT_REMINDER == 0.65
    assert ESTIMATED_ACTION_RECOVERY_PROB_PERSONALIZED_REMINDER == 0.78
    assert ESTIMATED_ACTION_RECOVERY_PROB_PAYMENT_LINK == 0.84


def test_action_scoring_bounds_and_components(high_value_high_intent_repeat_context):
    """Verify that action scoring returns valid bounds and attributes."""
    policy = get_recovery_policy()
    scored = score_single_action(
        action=RecoveryAction.PERSONALIZED_REMINDER,
        context=high_value_high_intent_repeat_context,
        policy=policy,
    )
    assert 0.0 <= scored.score <= 100.0
    assert scored.expected_recovery_value > 0.0
    assert 0.0 <= scored.estimated_recovery_probability <= 1.0
    assert scored.friction_level == "MEDIUM"


# ============================================================================
# 2. Decision Engine Rule & Scenario Tests
# ============================================================================

@pytest.mark.asyncio
async def test_high_value_high_intent_selects_active_recovery(high_value_high_intent_repeat_context):
    """
    Scenario: High-value + high-intent customer with repeat history
    Expectation: Selects PERSONALIZED_REMINDER (or PAYMENT_LINK), definitely not NO_ACTION.
    """
    policy = get_recovery_policy()
    eligible, excluded = filter_eligible_actions(high_value_high_intent_repeat_context, policy)
    scored = score_all_candidate_actions(high_value_high_intent_repeat_context, eligible, policy=policy)

    assert len(scored) >= 3
    top_action = scored[0].action
    assert top_action in (RecoveryAction.PERSONALIZED_REMINDER, RecoveryAction.PAYMENT_LINK)
    assert scored[0].score > 60.0


@pytest.mark.asyncio
async def test_low_value_low_intent_selects_no_action(low_value_low_intent_context):
    """
    Scenario: Low-value (₹45) + low-intent customer
    Expectation: Decision Engine selects NO_ACTION due to low score and falling below min expected value.
    """
    engine = RecoveryDecisionEngine()
    result = await engine.decide_recovery_action(
        event_data=low_value_low_intent_context.model_dump(),
        force_ai_fallback=True,
    )

    assert result.selected_action == RecoveryAction.NO_ACTION
    assert result.risk_score < 30.0


@pytest.mark.asyncio
async def test_high_intent_low_history_conservative_action(high_intent_zero_history_context):
    """
    Scenario: High intent but brand new customer (zero previous purchases).
    Expectation: Conservative non-intrusive action (CHECKOUT_REMINDER) or balanced action,
    avoiding overly aggressive payment links due to friction/penalty.
    """
    engine = RecoveryDecisionEngine()
    result = await engine.decide_recovery_action(
        event_data=high_intent_zero_history_context.model_dump(),
        force_ai_fallback=True,
    )

    assert result.selected_action in (RecoveryAction.CHECKOUT_REMINDER, RecoveryAction.PERSONALIZED_REMINDER)
    # Payment link should have lower score than checkout reminder for cold buyer
    alt_payment = next((a for a in result.alternative_actions if a.action == "PAYMENT_LINK"), None)
    if alt_payment:
        assert result.decision_score >= alt_payment.score


@pytest.mark.asyncio
async def test_payment_link_disabled_via_policy(high_value_high_intent_repeat_context):
    """
    Scenario: Merchant policy sets allow_payment_links = False
    Expectation: PAYMENT_LINK is marked NOT ELIGIBLE with explicit reason, and never selected.
    """
    strict_policy = {"allow_payment_links": False}
    engine = RecoveryDecisionEngine()
    result = await engine.decide_recovery_action(
        event_data=high_value_high_intent_repeat_context.model_dump(),
        policy_overrides=strict_policy,
        force_ai_fallback=True,
    )

    assert result.selected_action != RecoveryAction.PAYMENT_LINK
    # Check excluded actions
    payment_link_exclusion = next((e for e in result.excluded_actions if e.action == "PAYMENT_LINK"), None)
    assert payment_link_exclusion is not None
    assert "Disabled by merchant recovery policy" in payment_link_exclusion.reason


@pytest.mark.asyncio
async def test_expected_recovery_value_below_threshold_falls_back_to_no_action():
    """
    Scenario: Cart value is ₹150, but merchant sets minimum_expected_value = 500.
    Expectation: Active interventions are disqualified by policy; falls back to NO_ACTION.
    """
    small_cart_context = AIDecisionContext(
        event_id="evt_small_cart",
        customer_id="cust_small",
        session_id="sess_small",
        cart_value=150.0,
        currency="INR",
        payment_method="UPI",
        session_duration=300,
        pages_viewed=3,
        purchase_status="abandoned",
        previous_purchases=1,
        customer_lifetime_value=500.0,
        average_order_value=500.0,
        cart_abandonment_rate=0.2,
        total_sessions=2,
        risk_score=55.0,
        priority="MEDIUM",
        purchase_intent_score=50.0,
        revenue_at_risk=150.0,
        expected_recoverable_revenue=90.0,
    )

    high_threshold_policy = {"minimum_expected_value": 500.0}
    engine = RecoveryDecisionEngine()
    result = await engine.decide_recovery_action(
        event_data=small_cart_context.model_dump(),
        policy_overrides=high_threshold_policy,
        force_ai_fallback=True,
    )

    assert result.selected_action == RecoveryAction.NO_ACTION
    assert any("below" in e.reason.lower() for e in result.excluded_actions)


# ============================================================================
# 3. AI vs Decision Engine Divergence Detection Tests
# ============================================================================

def test_divergence_detection_explanation():
    """Verify divergence explanation when AI and Decision Engine recommend different actions."""
    policy = get_recovery_policy()
    ai_diag = AIDiagnosisResult(
        diagnosis=DiagnosisCategory.HIGH_VALUE_ABANDONMENT,
        recovery_probability=0.85,
        recommended_action=RecoveryAction.PAYMENT_LINK,
        priority=PriorityTier.CRITICAL,
        recommendation_confidence=0.90,
        reason_codes=["high_value"],
        explanation="High cart value",
        suggested_message="Pay here",
    )

    # Context where payment link is excluded due to policy
    policy_no_paylink = get_recovery_policy({"allow_payment_links": False})
    context = AIDecisionContext(
        event_id="evt_div_test",
        customer_id="cust_div",
        session_id="sess_div",
        cart_value=5000.0,
        currency="INR",
        payment_method="UPI",
        session_duration=500,
        pages_viewed=4,
        purchase_status="abandoned",
        previous_purchases=2,
        customer_lifetime_value=8000.0,
        average_order_value=4000.0,
        cart_abandonment_rate=0.2,
        total_sessions=3,
        risk_score=75.0,
        priority="HIGH",
        purchase_intent_score=70.0,
        revenue_at_risk=5000.0,
        expected_recoverable_revenue=4000.0,
    )

    eligible, excluded = filter_eligible_actions(context, policy_no_paylink)
    scored = score_single_action(RecoveryAction.PERSONALIZED_REMINDER, context, ai_diag, policy_no_paylink)

    divergence = evaluate_ai_divergence(
        ai_diagnosis=ai_diag,
        selected_action=RecoveryAction.PERSONALIZED_REMINDER,
        selected_score=scored,
        policy=policy_no_paylink,
        excluded_actions=excluded,
    )

    assert divergence is not None
    assert "AI suggested PAYMENT_LINK" in divergence
    assert "chose PERSONALIZED_REMINDER" in divergence


# ============================================================================
# 4. Database Persistence & Dual-Audit Integrity Tests
# ============================================================================

def test_dual_audit_persistence():
    """Verify that both AIDecision (Day 4) and RecoveryDecision (Day 5) coexist without overwrite."""
    init_db()
    db = SessionLocal()
    event_id = "evt_audit_coexist_999"

    try:
        # Save Day 4 AI decision
        ai_payload = {
            "decision_id": "ai_dec_999",
            "event_id": event_id,
            "customer_id": "cust_999",
            "diagnosis": "HIGH_PURCHASE_INTENT_ABANDONMENT",
            "recovery_probability": 0.82,
            "expected_recovery_value": 8200.0,
            "revenue_at_risk": 10000.0,
            "recommended_action": "PAYMENT_LINK",
            "priority": "HIGH",
            "recommendation_confidence": 0.88,
            "reason_codes": ["high_intent"],
            "explanation": "AI suggests payment link",
            "suggested_message": "Click here to pay",
            "source": "ai",
        }
        saved_ai = save_ai_decision(db, ai_payload)
        assert saved_ai.recommended_action == "PAYMENT_LINK"

        # Save Day 5 Decision Engine result (which selected PERSONALIZED_REMINDER)
        rec_payload = {
            "decision_id": "rec_dec_999",
            "event_id": event_id,
            "customer_id": "cust_999",
            "selected_action": "PERSONALIZED_REMINDER",
            "decision_score": 87.5,
            "expected_recovery_value": 7800.0,
            "estimated_recovery_probability": 0.78,
            "priority": "HIGH",
            "risk_score": 75.0,
            "reasons": ["High cart value", "Repeat customer history"],
            "explanation": "Decision engine chose personalized reminder for lower friction",
            "alternative_actions": [{"action": "PAYMENT_LINK", "score": 82.0}],
            "excluded_actions": [],
            "ai_recommended_action": "PAYMENT_LINK",
            "ai_recovery_probability": 0.82,
            "ai_diagnosis_category": "HIGH_PURCHASE_INTENT_ABANDONMENT",
            "divergence_reason": "AI suggested PAYMENT_LINK; decision engine chose PERSONALIZED_REMINDER",
            "policy_applied": DEFAULT_RECOVERY_POLICY,
        }
        saved_rec = save_recovery_decision(db, rec_payload)

        # Retrieve both from DB and verify neither was overwritten
        retrieved_ai = get_decision_by_event_id(db, event_id)
        retrieved_rec = get_recovery_decision_by_event_id(db, event_id)

        assert retrieved_ai is not None
        assert retrieved_ai.recommended_action == "PAYMENT_LINK"

        assert retrieved_rec is not None
        assert retrieved_rec.selected_action == "PERSONALIZED_REMINDER"
        assert retrieved_rec.ai_recommended_action == "PAYMENT_LINK"
        assert retrieved_rec.decision_score == 87.5

    finally:
        db.close()


# ============================================================================
# 5. API Endpoint Integration Tests
# ============================================================================

def test_api_decision_recommend_endpoint():
    """Verify POST /api/decision/recommend returns correct Day 5 schema and calculated values."""
    payload = {
        "event_data": {
            "event_id": "evt_api_test_001",
            "customer_id": "cust_api_001",
            "cart_value": 7500.0,
            "currency": "INR",
            "payment_method": "UPI",
            "session_duration": 850,
            "pages_viewed": 5,
            "purchase_status": "abandoned",
            "purchase_history": 2,
            "customer_lifetime_value": 15000.0,
            "cart_abandonment_rate": 0.20,
            "total_sessions": 4,
        }
    }

    response = client.post("/api/decision/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["event_id"] == "evt_api_test_001"
    assert data["selected_action"] in [a.value for a in RecoveryAction]
    assert "decision_score" in data
    assert "expected_recovery_value" in data
    assert "estimated_recovery_probability" in data
    assert "explanation" in data
    assert isinstance(data["reasons"], list)
    assert len(data["reasons"]) > 0
    assert isinstance(data["alternatives"], list)


def test_api_v1_decision_recommend_endpoint():
    """Verify versioned route POST /api/v1/decision/recommend works identically."""
    payload = {
        "event_data": {
            "event_id": "evt_v1_test_002",
            "customer_id": "cust_v1_002",
            "cart_value": 350.0,
            "session_duration": 60,
            "pages_viewed": 2,
            "purchase_status": "abandoned",
            "purchase_history": 0,
            "customer_lifetime_value": 0.0,
        }
    }

    response = client.post("/api/v1/decision/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "evt_v1_test_002"
    assert data["decision_score"] >= 0.0
