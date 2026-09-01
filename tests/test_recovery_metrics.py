"""
Unit Tests for Core Revenue Recovery Metrics (Day 9)
Tests revenue at risk, recovered revenue, recovery rates, average recovery value,
date filtering, and zero-division edge cases.
"""

import os
import sys
import pytest
import pandas as pd
from fastapi.testclient import TestClient

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.analytics.recovery_metrics import (
    get_revenue_at_risk,
    get_recovered_revenue,
    get_recovery_rate,
    get_average_recovery_value,
    filter_df_by_date,
    calculate_recovery_metrics,
    get_recovery_time_series,
)
from backend.app.main import app
from database.database import SessionLocal, init_db
from database.execution_models import RecoveryExecution, save_execution_record
from database.recovery_models import RecoveryRecord, save_recovery_record

client = TestClient(app)


def test_revenue_at_risk_calculation():
    """Verify revenue at risk accurately sums non-completed events."""
    sample_df = pd.DataFrame([
        {"event_id": "e1", "cart_value": 1000.0, "purchase_status": "abandoned"},
        {"event_id": "e2", "cart_value": 2500.0, "purchase_status": "failed"},
        {"event_id": "e3", "cart_value": 5000.0, "purchase_status": "completed"}, # excluded
    ])
    at_risk = get_revenue_at_risk(sample_df)
    assert at_risk == 3500.0


def test_recovery_rate_calculation():
    """Verify recovery rate handles ordinary ratios and 0%."""
    assert get_recovery_rate(2500.0, 10000.0) == 25.0
    assert get_recovery_rate(0.0, 10000.0) == 0.0
    assert get_recovery_rate(5000.0, 0.0) == 0.0 # Zero division safe
    assert get_recovery_rate(0.0, 0.0) == 0.0


def test_average_recovery_value_calculation():
    """Verify average recovery value handles zero recoveries gracefully."""
    assert get_average_recovery_value(15000.0, 5) == 3000.0
    assert get_average_recovery_value(0.0, 5) == 0.0
    assert get_average_recovery_value(5000.0, 0) == 0.0 # Zero division safe


def test_zero_division_handling_metrics():
    """Verify calculate_recovery_metrics never crashes with empty inputs."""
    empty_df = pd.DataFrame()
    metrics = calculate_recovery_metrics(events_df=empty_df)
    assert metrics.revenue_at_risk >= 0.0
    assert metrics.recovery_rate >= 0.0
    assert metrics.average_recovery_value >= 0.0


def test_time_range_date_filtering():
    """Verify date filter subsets dataframe properly."""
    sample_df = pd.DataFrame([
        {"event_id": "e1", "timestamp": "2026-08-30T10:00:00Z", "cart_value": 1000.0, "purchase_status": "abandoned"},
        {"event_id": "e2", "timestamp": "2026-08-20T10:00:00Z", "cart_value": 2000.0, "purchase_status": "abandoned"},
        {"event_id": "e3", "timestamp": "2026-07-01T10:00:00Z", "cart_value": 3000.0, "purchase_status": "abandoned"},
    ])
    filtered_7d = filter_df_by_date(sample_df, time_range="7d")
    assert len(filtered_7d) >= 1

    custom_filtered = filter_df_by_date(sample_df, start_date="2026-08-19", end_date="2026-08-25")
    assert len(custom_filtered) == 1
    assert custom_filtered.iloc[0]["event_id"] == "e2"


def test_recovery_time_series_trend():
    """Verify time series returns daily at_risk, recovered, attempts, and recovery_rate."""
    trend = get_recovery_time_series(days=14)
    assert len(trend) == 14
    point = trend[0]
    assert "date" in point
    assert "at_risk" in point
    assert "recovered" in point
    assert "recovery_rate" in point


def test_analytics_summary_endpoint():
    """Verify GET /api/analytics/summary returns single source of truth."""
    response = client.get("/api/analytics/summary?time_range=30d")
    assert response.status_code == 200
    data = response.json()
    assert "revenue_at_risk" in data
    assert "recovered_revenue" in data
    assert "observed_recovery" in data
    assert "estimated_incremental_recovery" in data
    assert "recovery_rate" in data
    assert data["revenue_at_risk"] > 0
