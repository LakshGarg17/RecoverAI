"""
ROI & Baseline Comparison Calculator (Day 9)
Computes Return on Investment, Net Recovery Value, configurable estimated action costs,
and honest comparison against a Simulated Baseline.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


# Default Estimated Operating Cost Assumptions (INR)
DEFAULT_COST_ASSUMPTIONS: Dict[str, float] = {
    "PAYMENT_LINK": 2.50,            # Razorpay API link generation + webhook processing
    "PERSONALIZED_REMINDER": 0.35,   # LLM inference token cost + SMS/WhatsApp dispatch
    "CHECKOUT_REMINDER": 0.15,       # Push notification / lightweight SMS
    "DELAYED_FOLLOW_UP": 0.15,       # Scheduled queue execution
    "NO_ACTION": 0.00,               # Bounded block / zero outreach
    "DEFAULT_PER_ATTEMPT_COST": 0.65, # Weighted average operating cost per attempt
}


class CostAssumptions(BaseModel):
    """Configurable cost assumptions schema."""
    payment_link_cost: float = Field(2.50, description="Estimated Razorpay API & processing cost per link (INR).")
    personalized_reminder_cost: float = Field(0.35, description="Estimated LLM inference + message dispatch cost (INR).")
    checkout_reminder_cost: float = Field(0.15, description="Estimated notification cost per reminder (INR).")
    delayed_follow_up_cost: float = Field(0.15, description="Estimated queued dispatch cost (INR).")
    average_cost_per_attempt: float = Field(0.65, description="Weighted average operating cost per recovery action (INR).")


class ROIBreakdown(BaseModel):
    """ROI calculation outcome schema."""
    gross_recovered_revenue: float = Field(0.0, description="Gross recovered revenue in INR.")
    total_recovery_attempts: int = Field(0, description="Total recovery interventions dispatched.")
    estimated_operating_cost: float = Field(0.0, description="Total estimated operating cost of recovery actions in INR.")
    net_recovery_value: float = Field(0.0, description="Net value generated = Gross Recovered - Operating Cost.")
    roi_percentage: float = Field(0.0, description="Return on Investment = (Net Value / Operating Cost) * 100.")
    cost_per_recovered_rupee: float = Field(0.0, description="Cost incurred per ₹1.00 of recovered revenue.")
    currency: str = "INR"
    cost_methodology_note: str = (
        "Operating costs are estimated based on standard SMS/WhatsApp carrier fees (₹0.15-0.35/msg) "
        "and payment gateway API processing overhead (₹2.50/link), not measured invoices."
    )


class MetricComparison(BaseModel):
    """Single metric comparison row."""
    metric_name: str
    simulated_baseline: str
    recoverai: str
    lift: str


class BaselineComparisonResult(BaseModel):
    """Side-by-side comparison between Simulated Baseline and RecoverAI."""
    comparison_table: list[MetricComparison]
    simulated_baseline_revenue: float
    recoverai_observed_revenue: float
    estimated_incremental_revenue: float
    recovery_rate_lift_multiplier: float
    methodology_disclaimer: str = (
        "Simulated Baseline represents historical organic checkout recovery without active intervention (~1.2% rate). "
        "Estimated Incremental Recovery is an observational estimate comparing RecoverAI against this baseline, "
        "not a causal randomized control trial (RCT)."
    )


def calculate_roi(
    recovered_revenue: float,
    total_attempts: int,
    action_breakdown: Optional[Dict[str, int]] = None,
    cost_overrides: Optional[Dict[str, float]] = None,
) -> ROIBreakdown:
    """
    Computes Net Recovery Value, Estimated Costs, and ROI Percentage.
    Handles zero division, negative ROI, and edge cases gracefully.
    """
    costs = dict(DEFAULT_COST_ASSUMPTIONS)
    if cost_overrides:
        costs.update(cost_overrides)

    total_cost = 0.0
    if action_breakdown:
        for action, count in action_breakdown.items():
            unit_cost = costs.get(action, costs["DEFAULT_PER_ATTEMPT_COST"])
            total_cost += count * unit_cost
    else:
        total_cost = total_attempts * costs["DEFAULT_PER_ATTEMPT_COST"]

    total_cost = round(total_cost, 2)
    net_value = round(recovered_revenue - total_cost, 2)

    # ROI % = (Net Recovery Value / Operating Cost) * 100
    if total_cost > 0:
        roi_pct = round((net_value / total_cost) * 100.0, 2)
        cost_per_rupee = round(total_cost / recovered_revenue, 4) if recovered_revenue > 0 else 0.0
    else:
        roi_pct = 0.0 if recovered_revenue <= 0 else 100.0
        cost_per_rupee = 0.0

    return ROIBreakdown(
        gross_recovered_revenue=round(recovered_revenue, 2),
        total_recovery_attempts=total_attempts,
        estimated_operating_cost=total_cost,
        net_recovery_value=net_value,
        roi_percentage=roi_pct,
        cost_per_recovered_rupee=cost_per_rupee,
        currency="INR",
    )


def get_baseline_comparison(
    revenue_at_risk: float,
    recovered_revenue: float,
    total_attempts: int,
    successful_recoveries: int,
    spontaneous_baseline_rate: float = 0.012, # 1.2% historical organic checkout completion
) -> BaselineComparisonResult:
    """
    Builds a structured side-by-side comparison table between:
    - Simulated Baseline (no automated recovery intervention)
    - RecoverAI (autonomous diagnosis, guardrails, and execution)
    """
    # 1. Simulated Baseline calculations
    baseline_recovered_rev = round(revenue_at_risk * spontaneous_baseline_rate, 2)
    baseline_success_count = int(round(total_attempts * spontaneous_baseline_rate)) if total_attempts > 0 else 0
    baseline_avg_val = round(baseline_recovered_rev / max(1, baseline_success_count), 2) if baseline_success_count > 0 else 0.0
    baseline_recovery_rate = round(spontaneous_baseline_rate * 100.0, 2)

    # 2. RecoverAI calculations
    recoverai_rate = round((recovered_revenue / revenue_at_risk * 100.0), 2) if revenue_at_risk > 0 else 0.0
    recoverai_avg_val = round(recovered_revenue / max(1, successful_recoveries), 2) if successful_recoveries > 0 else 0.0
    estimated_incremental = round(max(0.0, recovered_revenue - baseline_recovered_rev), 2)
    lift_multiplier = round(recoverai_rate / max(0.01, baseline_recovery_rate), 1)

    table = [
        MetricComparison(
            metric_name="Recovery Rate (%)",
            simulated_baseline=f"{baseline_recovery_rate:.2f}%",
            recoverai=f"{recoverai_rate:.2f}%",
            lift=f"+{recoverai_rate - baseline_recovery_rate:.2f}% ({lift_multiplier}x lift)",
        ),
        MetricComparison(
            metric_name="Recovered Revenue (INR)",
            simulated_baseline=f"₹{baseline_recovered_rev:,.2f}",
            recoverai=f"₹{recovered_revenue:,.2f}",
            lift=f"+₹{estimated_incremental:,.2f} incremental",
        ),
        MetricComparison(
            metric_name="Recovery Attempts",
            simulated_baseline="0 (No Outreach)",
            recoverai=f"{total_attempts:,} actions",
            lift="Targeted Proactive Dunning",
        ),
        MetricComparison(
            metric_name="Average Recovery Value",
            simulated_baseline=f"₹{baseline_avg_val:,.2f}",
            recoverai=f"₹{recoverai_avg_val:,.2f}",
            lift=f"+₹{max(0.0, recoverai_avg_val - baseline_avg_val):,.2f}/order",
        ),
    ]

    return BaselineComparisonResult(
        comparison_table=table,
        simulated_baseline_revenue=baseline_recovered_rev,
        recoverai_observed_revenue=round(recovered_revenue, 2),
        estimated_incremental_revenue=estimated_incremental,
        recovery_rate_lift_multiplier=lift_multiplier,
    )
