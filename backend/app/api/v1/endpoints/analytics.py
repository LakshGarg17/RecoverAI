"""
Analytics & Proof-of-Recovery Endpoints (Day 9)
Exposes single source of truth analytics for core revenue metrics, ROI calculation,
per-action performance, and risk score calibration.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from backend.analytics.recovery_metrics import (
    calculate_recovery_metrics,
    get_recovery_time_series,
    RecoveryMetricsSummary,
)
from backend.analytics.roi_calculator import (
    calculate_roi,
    get_baseline_comparison,
    ROIBreakdown,
    BaselineComparisonResult,
)
from backend.analytics.ai_evaluation import (
    evaluate_ai_actions,
    calculate_ai_action_success_rate,
    calculate_risk_calibration,
    generate_merchant_insights,
    ActionPerformance,
    RiskBucketPerformance,
    AIEvaluationReport,
)

router = APIRouter()


@router.get(
    "/summary",
    response_model=RecoveryMetricsSummary,
    summary="Get Core Revenue Recovery Metrics",
    description="Returns single source of truth for revenue at risk, recovered revenue, recovery rate, and average recovery value."
)
def get_analytics_summary_endpoint(
    time_range: str = Query(default="30d", pattern="^(today|7d|30d|all)$"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD custom start date"),

    end_date: Optional[str] = Query(None, description="YYYY-MM-DD custom end date"),
    db: Session = Depends(get_db),
) -> RecoveryMetricsSummary:
    return calculate_recovery_metrics(
        db=db,
        time_range=time_range,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/actions",
    response_model=List[ActionPerformance],
    summary="Get Per-Action Performance Breakdown",
    description="Returns conversion performance and revenue recovered across all 5 recovery action enums."
)
def get_action_performance_endpoint(
    db: Session = Depends(get_db),
) -> List[ActionPerformance]:
    return evaluate_ai_actions(db=db)


@router.get(
    "/risk-performance",
    response_model=List[RiskBucketPerformance],
    summary="Get Risk Score Calibration Performance",
    description="Returns conversion rates across 5 risk brackets (0-20, 21-40, 41-60, 61-80, 81-100)."
)
def get_risk_calibration_endpoint(
    db: Session = Depends(get_db),
) -> List[RiskBucketPerformance]:
    return calculate_risk_calibration(db=db)


@router.get(
    "/roi",
    summary="Get Return on Investment & Baseline Comparison",
    description="Computes Net Recovery Value, Estimated Operating Costs, ROI %, and Simulated Baseline comparison."
)
def get_roi_analytics_endpoint(
    time_range: str = Query(default="30d"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    metrics = calculate_recovery_metrics(db=db, time_range=time_range)
    actions = evaluate_ai_actions(db=db)
    
    action_counts = {a.action: a.attempts for a in actions}
    roi_breakdown: ROIBreakdown = calculate_roi(
        recovered_revenue=metrics.recovered_revenue,
        total_attempts=metrics.recovery_attempts,
        action_breakdown=action_counts,
    )

    baseline_comparison: BaselineComparisonResult = get_baseline_comparison(
        revenue_at_risk=metrics.revenue_at_risk,
        recovered_revenue=metrics.recovered_revenue,
        total_attempts=metrics.recovery_attempts,
        successful_recoveries=metrics.successful_recoveries,
    )

    return {
        "roi": roi_breakdown.model_dump(),
        "baseline_comparison": baseline_comparison.model_dump(),
    }


@router.get(
    "/ai-evaluation",
    response_model=AIEvaluationReport,
    summary="Get Comprehensive AI Evaluation Report",
    description="Returns AI Action Success Rate, per-action table, risk calibration buckets, and generated merchant insights."
)
def get_ai_evaluation_report_endpoint(
    db: Session = Depends(get_db),
) -> AIEvaluationReport:
    metrics = calculate_recovery_metrics(db=db)
    actions = evaluate_ai_actions(db=db)
    risk_buckets = calculate_risk_calibration(db=db)
    success_rate = calculate_ai_action_success_rate(db=db)
    takeaways = generate_merchant_insights(actions, risk_buckets)

    return AIEvaluationReport(
        ai_action_success_rate=success_rate,
        total_ai_actions_executed=metrics.recovery_attempts,
        total_successful_ai_recoveries=metrics.successful_recoveries,
        total_revenue_influenced=metrics.recovered_revenue,
        action_performances=actions,
        risk_calibration_buckets=risk_buckets,
        merchant_takeaways=takeaways,
    )


@router.get(
    "/trend",
    summary="Get Extended Recovery Trend with Rate %",
    description="Returns daily time series containing Revenue at Risk, Recovered Revenue, Attempts, and Recovery Rate %."
)
def get_analytics_trend_endpoint(
    days: int = Query(default=14, ge=7, le=30),
) -> List[Dict[str, Any]]:
    return get_recovery_time_series(days=days)
