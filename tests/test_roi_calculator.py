"""
Unit Tests for ROI Calculator & Baseline Comparison (Day 9)
Tests positive ROI, zero cost, zero recovery, cost exceeding recovery,
and honest simulated baseline comparison table.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.analytics.roi_calculator import (
    calculate_roi,
    get_baseline_comparison,
    ROIBreakdown,
    BaselineComparisonResult,
)
from backend.app.main import app

client = TestClient(app)


def test_positive_roi_calculation():
    """Verify ROI % when recovered revenue exceeds operating costs."""
    # ₹100,000 recovered with 500 attempts @ ₹0.65 avg = ₹325 cost
    roi = calculate_roi(recovered_revenue=100000.0, total_attempts=500)
    assert roi.gross_recovered_revenue == 100000.0
    assert roi.estimated_operating_cost == 325.0
    assert roi.net_recovery_value == 99675.0
    assert roi.roi_percentage > 30000.0 # ~30,669%


def test_zero_cost_roi_calculation():
    """Verify ROI handles zero cost attempts without dividing by zero."""
    roi = calculate_roi(recovered_revenue=5000.0, total_attempts=0)
    assert roi.estimated_operating_cost == 0.0
    assert roi.net_recovery_value == 5000.0
    assert roi.roi_percentage == 100.0


def test_zero_recovery_negative_roi_calculation():
    """Verify negative Net Recovery Value and negative ROI when 0 revenue recovered."""
    roi = calculate_roi(recovered_revenue=0.0, total_attempts=100)
    assert roi.gross_recovered_revenue == 0.0
    assert roi.estimated_operating_cost == 65.0
    assert roi.net_recovery_value == -65.0
    assert roi.roi_percentage == -100.0


def test_cost_exceeding_recovery_roi():
    """Verify negative ROI when cost exceeds recovered revenue."""
    roi = calculate_roi(
        recovered_revenue=100.0,
        total_attempts=200,
        cost_overrides={"DEFAULT_PER_ATTEMPT_COST": 2.0} # cost = ₹400
    )
    assert roi.estimated_operating_cost == 400.0
    assert roi.net_recovery_value == -300.0
    assert roi.roi_percentage == -75.0


def test_simulated_baseline_comparison():
    """Verify honest baseline comparison table and lift multiplier."""
    res: BaselineComparisonResult = get_baseline_comparison(
        revenue_at_risk=4500000.0,
        recovered_revenue=180000.0,
        total_attempts=800,
        successful_recoveries=60,
    )
    assert res.simulated_baseline_revenue == 54000.0 # 1.2% of 4.5M
    assert res.recoverai_observed_revenue == 180000.0
    assert res.estimated_incremental_revenue == 126000.0
    assert len(res.comparison_table) >= 4
    assert "Simulated Baseline" in res.methodology_disclaimer


def test_analytics_roi_endpoint():
    """Verify GET /api/analytics/roi returns both roi breakdown and baseline comparison."""
    response = client.get("/api/analytics/roi?time_range=30d")
    assert response.status_code == 200
    data = response.json()
    assert "roi" in data
    assert "baseline_comparison" in data
    assert "net_recovery_value" in data["roi"]
    assert "comparison_table" in data["baseline_comparison"]
