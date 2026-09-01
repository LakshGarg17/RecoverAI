"""
Unit & Integration Tests for Day 8 Dashboard Analytics & Recovery Endpoints
Tests summary KPIs, trends, conversion funnel, AI insights, opportunities table, case detail, policy, and audit endpoints.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app.main import app

client = TestClient(app)


def test_dashboard_summary_endpoint():
    """Verify GET /api/dashboard/summary returns valid KPIs."""
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "revenue_at_risk" in data
    assert "recovered_revenue" in data
    assert "recovery_rate" in data
    assert "active_recoveries" in data
    assert "blocked_recoveries" in data
    assert data["revenue_at_risk"] > 0
    assert data["currency"] == "INR"


def test_dashboard_recovery_trend_endpoint():
    """Verify GET /api/dashboard/recovery-trend returns 14-day time series."""
    response = client.get("/api/dashboard/recovery-trend?days=14")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first_item = data[0]
    assert "date" in first_item
    assert "at_risk" in first_item
    assert "recovered" in first_item
    assert "attempts" in first_item


def test_dashboard_funnel_endpoint():
    """Verify GET /api/dashboard/funnel returns 5 stages with conversion rates."""
    response = client.get("/api/dashboard/funnel")
    assert response.status_code == 200
    data = response.json()
    assert "stages" in data
    stages = data["stages"]
    assert len(stages) == 5
    stage_names = [s["stage"] for s in stages]
    assert "Revenue At Risk" in stage_names
    assert "Revenue Recovered" in stage_names


def test_dashboard_ai_insights_endpoint():
    """Verify GET /api/dashboard/ai-insights returns action distributions and top causes."""
    response = client.get("/api/dashboard/ai-insights")
    assert response.status_code == 200
    data = response.json()
    assert "top_recovery_reason" in data
    assert "action_distribution" in data
    assert isinstance(data["action_distribution"], list)
    assert len(data["action_distribution"]) >= 3


def test_recovery_opportunities_endpoint():
    """Verify GET /api/recovery/opportunities supports pagination and filters."""
    response = client.get("/api/recovery/opportunities?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert len(data["items"]) <= 10
    if data["items"]:
        item = data["items"][0]
        assert "event_id" in item
        assert "amount" in item
        assert "risk_score" in item
        assert "ai_action" in item
        assert "guardrail_status" in item


def test_recovery_detail_endpoint():
    """Verify GET /api/recovery/detail/{id} returns joined full diagnostic record."""
    response = client.get("/api/recovery/detail/evt_000004")
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "evt_000004"
    assert "cart_value" in data
    assert "risk_score" in data
    assert "checks" in data
    assert "timeline" in data
    assert isinstance(data["timeline"], list)
    assert len(data["timeline"]) >= 3


def test_recovery_demo_cases_endpoint():
    """Verify GET /api/recovery/demo-cases returns curated demo scenarios."""
    response = client.get("/api/recovery/demo-cases")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_guardrails_policy_endpoint():
    """Verify GET /api/guardrails/policy returns merchant policy thresholds."""
    response = client.get("/api/guardrails/policy")
    assert response.status_code == 200
    data = response.json()
    assert "policy_version" in data
    assert "max_recovery_attempts" in data
    assert "cooldown_minutes" in data
    assert "minimum_risk_score" in data
    assert "allow_payment_link" in data


def test_transactions_endpoint():
    """Verify GET /api/transactions returns paginated transaction list."""
    response = client.get("/api/transactions?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_audit_logs_endpoint():
    """Verify GET /api/audit/logs returns paginated audit events."""
    response = client.get("/api/audit/logs?page=1&limit=15")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
