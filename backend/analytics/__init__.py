"""
RecoverAI Analytics & Evaluation Module (Day 9)
Provides single source of truth for revenue metrics, ROI calculation, AI action evaluation,
and risk score calibration.
"""

from .recovery_metrics import (
    calculate_recovery_metrics,
    get_revenue_at_risk,
    get_recovered_revenue,
    get_recovery_rate,
    get_average_recovery_value,
    get_recovery_time_series,
    RecoveryMetricsSummary,
)
from .roi_calculator import (
    calculate_roi,
    get_baseline_comparison,
    ROIBreakdown,
    BaselineComparisonResult,
)
from .ai_evaluation import (
    evaluate_ai_actions,
    calculate_ai_action_success_rate,
    calculate_risk_calibration,
    generate_merchant_insights,
    ActionPerformance,
    RiskBucketPerformance,
)

__all__ = [
    "calculate_recovery_metrics",
    "get_revenue_at_risk",
    "get_recovered_revenue",
    "get_recovery_rate",
    "get_average_recovery_value",
    "get_recovery_time_series",
    "RecoveryMetricsSummary",
    "calculate_roi",
    "get_baseline_comparison",
    "ROIBreakdown",
    "BaselineComparisonResult",
    "evaluate_ai_actions",
    "calculate_ai_action_success_rate",
    "calculate_risk_calibration",
    "generate_merchant_insights",
    "ActionPerformance",
    "RiskBucketPerformance",
]
