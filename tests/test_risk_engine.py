"""
Unit and Integration Tests for RecoverAI Revenue Risk Engine (Day 3)
Tests deterministic scoring rules, weights, priority categorization, and expected recoverable revenue.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

# Ensure backend root is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.services.risk_engine import (
    evaluate_event_risk,
    batch_evaluate_events,
    compute_cart_value_score,
    compute_customer_history_score,
    compute_engagement_score,
    compute_recency_score,
    classify_priority,
    compute_expected_recoverable_revenue,
    WEIGHT_CART_VALUE,
    WEIGHT_PURCHASE_INTENT,
    WEIGHT_CUSTOMER_HISTORY,
    WEIGHT_ENGAGEMENT,
    WEIGHT_RECENCY,
)
from app.schemas.risk import RiskEvaluationResponse, RiskScoreBreakdown


def test_scoring_weights_sum_to_one():
    """Verify that deterministic component weights exactly equal 100% (1.0)."""
    total_weight = (
        WEIGHT_CART_VALUE +
        WEIGHT_PURCHASE_INTENT +
        WEIGHT_CUSTOMER_HISTORY +
        WEIGHT_ENGAGEMENT +
        WEIGHT_RECENCY
    )
    assert abs(total_weight - 1.0) < 1e-6
    assert WEIGHT_CART_VALUE == 0.25
    assert WEIGHT_PURCHASE_INTENT == 0.30
    assert WEIGHT_CUSTOMER_HISTORY == 0.20
    assert WEIGHT_ENGAGEMENT == 0.15
    assert WEIGHT_RECENCY == 0.10


def test_cart_value_score_bounds_and_scaling():
    """Verify cart value scoring clamps to [0, 100] and scales properly."""
    assert compute_cart_value_score(0.0) == 0.0
    assert compute_cart_value_score(-100.0) == 0.0
    assert compute_cart_value_score(1750.0) == 50.0
    assert compute_cart_value_score(3500.0) == 100.0
    assert compute_cart_value_score(10000.0) == 100.0


def test_customer_history_score_repeat_vs_first_time():
    """Verify repeat customer scores higher than first-time visitor with identical cart."""
    # First-time visitor: 0 prior orders, 0 CLV, 1 session
    score_first = compute_customer_history_score(
        purchase_history=0,
        customer_lifetime_value=0.0,
        total_sessions=1
    )
    # Loyal repeat buyer: 3 prior orders, 4000 CLV, 5 sessions
    score_loyal = compute_customer_history_score(
        purchase_history=3,
        customer_lifetime_value=4000.0,
        total_sessions=5
    )

    assert score_loyal > score_first
    assert score_loyal == 100.0
    assert score_first < 20.0


def test_engagement_score_duration_and_pages():
    """Verify engagement score scales with dwell time, page breadth, and cart action."""
    score_low = compute_engagement_score(session_duration=60, pages_viewed=2, has_cart=False)
    score_high = compute_engagement_score(session_duration=1500, pages_viewed=20, has_cart=True)

    assert 0.0 <= score_low <= 100.0
    assert 0.0 <= score_high <= 100.0
    assert score_high == 100.0
    assert score_low < 15.0


def test_recency_score_step_function():
    """Verify recency decay score buckets match design specification."""
    assert compute_recency_score(recency_hours=0.5) == 100.0  # < 1 hour
    assert compute_recency_score(recency_hours=3.0) == 80.0   # 1-6 hours
    assert compute_recency_score(recency_hours=12.0) == 60.0  # 6-24 hours
    assert compute_recency_score(recency_hours=48.0) == 30.0  # 1-3 days
    assert compute_recency_score(recency_hours=96.0) == 10.0  # > 3 days


def test_priority_tier_classification():
    """Verify threshold boundary mapping for operational urgency priority tiers."""
    assert classify_priority(95.0) == "CRITICAL"
    assert classify_priority(80.0) == "CRITICAL"
    assert classify_priority(79.9) == "HIGH"
    assert classify_priority(60.0) == "HIGH"
    assert classify_priority(59.9) == "MEDIUM"
    assert classify_priority(40.0) == "MEDIUM"
    assert classify_priority(39.9) == "LOW"
    assert classify_priority(0.0) == "LOW"


def test_expected_recoverable_revenue_calculation():
    """Verify Expected Recoverable Revenue = cart_value * (purchase_intent_score / 100)."""
    # 10,000 INR cart with 85% purchase intent probability
    rev = compute_expected_recoverable_revenue(cart_value=10000.0, purchase_intent_score=85.0)
    assert rev == 8500.0

    # 5,000 INR cart with 50% purchase intent
    rev_mid = compute_expected_recoverable_revenue(cart_value=5000.0, purchase_intent_score=50.0)
    assert rev_mid == 2500.0

    # Zero cart value
    assert compute_expected_recoverable_revenue(cart_value=0.0, purchase_intent_score=90.0) == 0.0


def test_single_event_risk_evaluation():
    """Verify end-to-end evaluation of a single event dictionary and Pydantic validation."""
    sample_event = {
        "event_id": "evt_001024",
        "customer_id": "cust_01803",
        "session_id": "sess_001024",
        "amount": 14999.0,
        "currency": "INR",
        "payment_method": "UPI",
        "event_type": "cart_abandoned",
        "purchase_status": "abandoned",
        "cart_value": 14999.0,
        "session_duration": 1400,
        "pages_viewed": 19,
        "purchase_history": 2,
        "customer_lifetime_value": 4500.0,
        "purchase_intent_score": 88.0,
        "revenue_at_risk": 14999.0,
        "recency_hours": 2.0,
    }

    result = evaluate_event_risk(sample_event)

    # Validate output schema
    validated = RiskEvaluationResponse(**result)
    assert validated.event_id == "evt_001024"
    assert validated.customer_id == "cust_01803"
    assert validated.revenue_at_risk == 14999.0
    assert validated.expected_recoverable_revenue == round(14999.0 * 0.88, 2)
    assert validated.risk_score >= 80.0
    assert validated.priority == "CRITICAL"
    assert validated.recovery_candidate is True
    assert validated.score_breakdown.cart_value_score == 100.0
    assert validated.score_breakdown.recency_score == 80.0


def test_batch_evaluate_events_dataframe():
    """Verify batch evaluation over a pandas DataFrame adds all required columns."""
    mock_df = pd.DataFrame([
        {
            "event_id": "evt_000001",
            "customer_id": "cust_00001",
            "event_type": "cart_abandoned",
            "purchase_status": "abandoned",
            "cart_value": 3500.0,
            "session_duration": 1200,
            "pages_viewed": 18,
            "purchase_history": 3,
            "customer_lifetime_value": 4000.0,
            "purchase_intent_score": 85.0,
            "revenue_at_risk": 3500.0,
        },
        {
            "event_id": "evt_000002",
            "customer_id": "cust_00002",
            "event_type": "page_browse",
            "purchase_status": "browsing",
            "cart_value": 0.0,
            "session_duration": 100,
            "pages_viewed": 2,
            "purchase_history": 0,
            "customer_lifetime_value": 0.0,
            "purchase_intent_score": 10.0,
            "revenue_at_risk": 0.0,
        }
    ])

    evaluated = batch_evaluate_events(mock_df)

    assert "risk_score" in evaluated.columns
    assert "priority" in evaluated.columns
    assert "expected_recoverable_revenue" in evaluated.columns
    assert "recovery_candidate" in evaluated.columns

    # Event 1: Active abandoned cart
    assert evaluated.loc[0, "recovery_candidate"] == True
    assert evaluated.loc[0, "priority"] in ["CRITICAL", "HIGH"]
    assert evaluated.loc[0, "expected_recoverable_revenue"] == round(3500.0 * 0.85, 2)

    # Event 2: Page browse only
    assert evaluated.loc[1, "recovery_candidate"] == False
    assert evaluated.loc[1, "expected_recoverable_revenue"] == 0.0
    assert evaluated.loc[1, "priority"] == "LOW"
