"""
Unit Tests for AI Evaluation & Risk Score Calibration (Day 9)
Tests AI action success rate, per-action comparison, risk score calibration brackets,
and generated merchant insights.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.analytics.ai_evaluation import (
    evaluate_ai_actions,
    calculate_ai_action_success_rate,
    calculate_risk_calibration,
    generate_merchant_insights,
)
from backend.app.main import app

client = TestClient(app)


def test_ai_action_success_rate():
    """Verify AI Action Success Rate metric returns valid percentage."""
    rate = calculate_ai_action_success_rate(db=None)
    assert 0.0 <= rate <= 100.0


def test_evaluate_ai_actions_all_enums():
    """Verify all 5 action enums are evaluated with valid fields."""
    actions = evaluate_ai_actions(db=None)
    assert len(actions) == 5
    action_names = {a.action for a in actions}
    expected = {
        "PAYMENT_LINK",
        "PERSONALIZED_REMINDER",
        "CHECKOUT_REMINDER",
        "DELAYED_FOLLOW_UP",
        "NO_ACTION",
    }
    assert action_names == expected
    for a in actions:
        assert a.display_name != ""
        assert a.recovery_rate >= 0.0
        assert a.revenue_recovered >= 0.0


def test_risk_calibration_5_buckets():
    """Verify 5 risk brackets (0-20, 21-40, 41-60, 61-80, 81-100)."""
    buckets = calculate_risk_calibration(db=None)
    assert len(buckets) == 5
    labels = [b.bucket for b in buckets]
    assert labels == ["0–20", "21–40", "41–60", "61–80", "81–100"]

    # Verify monotonic / higher correlation in higher brackets
    high_tier = next(b for b in buckets if b.bucket == "81–100")
    low_tier = next(b for b in buckets if b.bucket == "21–40")
    assert high_tier.recovery_rate > low_tier.recovery_rate
    assert high_tier.revenue_recovered > low_tier.revenue_recovered


def test_merchant_insights_generation():
    """Verify merchant insights generate data-backed takeaways."""
    actions = evaluate_ai_actions(db=None)
    buckets = calculate_risk_calibration(db=None)
    takeaways = generate_merchant_insights(actions, buckets)
    assert len(takeaways) >= 2
    assert any("conversion rate" in t.lower() or "recovery" in t.lower() for t in takeaways)


def test_analytics_ai_evaluation_endpoint():
    """Verify GET /api/analytics/ai-evaluation returns complete evaluation schema."""
    response = client.get("/api/analytics/ai-evaluation")
    assert response.status_code == 200
    data = response.json()
    assert "ai_action_success_rate" in data
    assert "action_performances" in data
    assert "risk_calibration_buckets" in data
    assert "merchant_takeaways" in data
    assert len(data["action_performances"]) == 5
    assert len(data["risk_calibration_buckets"]) == 5


def test_analytics_actions_endpoint():
    """Verify GET /api/analytics/actions returns list of action performances."""
    response = client.get("/api/analytics/actions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


def test_analytics_risk_performance_endpoint():
    """Verify GET /api/analytics/risk-performance returns 5 risk brackets."""
    response = client.get("/api/analytics/risk-performance")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
