"""
Batch Risk Engine Evaluation and Portfolio Metrics Reporter (Day 3)
Evaluates data/processed/recoverai_events.csv and generates business metrics.
"""

import os
import sys
import pandas as pd
import numpy as np

# Ensure backend root is on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
backend_dir = os.path.join(root_dir, "backend")
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.services.risk_engine import evaluate_event_risk, batch_evaluate_events


def get_data_paths():
    processed_path = os.path.join(root_dir, "data", "processed", "recoverai_events.csv")
    enriched_path = os.path.join(root_dir, "data", "processed", "recoverai_risk_evaluated.csv")
    return {
        "processed_path": processed_path,
        "enriched_path": enriched_path,
    }


def run_portfolio_risk_evaluation(file_path: str = None) -> dict:
    """
    Evaluates risk and recoverable revenue across the canonical events dataset.
    Prints banner-style portfolio summary and returns metrics dict.
    """
    paths = get_data_paths()
    if file_path is None:
        file_path = paths["processed_path"]

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Processed dataset not found at '{file_path}'. "
            f"Please run 'python backend/data_pipeline/run_pipeline.py' first."
        )

    print("\n" + "=" * 70)
    print(" RecoverAI Revenue Risk Engine — Portfolio Evaluation Report")
    print("=" * 70)

    raw_events_df = pd.read_csv(file_path)
    evaluated_df = batch_evaluate_events(raw_events_df)

    total_events = len(evaluated_df)
    abandoned_df = evaluated_df[evaluated_df["event_type"] == "cart_abandoned"]
    candidates_df = evaluated_df[evaluated_df["recovery_candidate"] == True]

    total_at_risk = float(abandoned_df["revenue_at_risk"].sum())
    total_expected_recoverable = float(abandoned_df["expected_recoverable_revenue"].sum())
    efficiency_pct = (total_expected_recoverable / total_at_risk * 100.0) if total_at_risk > 0 else 0.0

    print(f" Dataset Analyzed             : {os.path.basename(file_path)}")
    print(f" Total Sessions / Events      : {total_events:,}")
    print(f" Cart Abandonment Events      : {len(abandoned_df):,} ({len(abandoned_df)/total_events*100:.1f}%)")
    print(f" Qualified Recovery Candidates: {len(candidates_df):,} ({len(candidates_df)/len(abandoned_df)*100:.1f}% of abandoned carts)")
    print("-" * 70)
    print(f" POTENTIAL REVENUE AT RISK    : INR {total_at_risk:,.2f}")
    print(f" EXPECTED RECOVERABLE REVENUE : INR {total_expected_recoverable:,.2f}")
    print(f" Portfolio Recovery Potential : {efficiency_pct:.2f}%")
    print("=" * 70)

    # Priority Tier Distribution (among abandoned carts)
    print("\n Urgency Priority Tier Distribution (Abandoned Carts):")
    print("-" * 70)
    print(f" {'Tier':<10} | {'Count':<7} | {'Share %':<8} | {'Revenue at Risk':<18} | {'Expected Recoverable':<20} | {'Avg Risk'}")
    print("-" * 70)

    tier_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    tier_metrics = {}

    for tier in tier_order:
        sub = abandoned_df[abandoned_df["priority"] == tier]
        cnt = len(sub)
        share = (cnt / len(abandoned_df) * 100.0) if len(abandoned_df) > 0 else 0.0
        risk_rev = float(sub["revenue_at_risk"].sum())
        exp_rev = float(sub["expected_recoverable_revenue"].sum())
        avg_score = float(sub["risk_score"].mean()) if cnt > 0 else 0.0

        tier_metrics[tier] = {
            "count": cnt,
            "share_pct": round(share, 2),
            "potential_revenue_at_risk": round(risk_rev, 2),
            "expected_recoverable_revenue": round(exp_rev, 2),
            "avg_risk_score": round(avg_score, 2),
        }

        print(f" {tier:<10} | {cnt:>7,} | {share:>7.1f}% | INR {risk_rev:>14,.2f} | INR {exp_rev:>16,.2f} | {avg_score:>6.1f}")
    print("-" * 70)

    # Payment Method Breakdown
    print("\n Breakdown by Payment Instrument (Abandoned Carts):")
    print("-" * 70)
    print(f" {'Payment Method':<14} | {'Events':<7} | {'Revenue at Risk':<18} | {'Expected Recoverable':<20} | {'Avg Intent'}")
    print("-" * 70)
    pay_methods = abandoned_df["payment_method"].unique()
    for method in sorted(pay_methods):
        sub_p = abandoned_df[abandoned_df["payment_method"] == method]
        p_cnt = len(sub_p)
        p_risk = float(sub_p["revenue_at_risk"].sum())
        p_exp = float(sub_p["expected_recoverable_revenue"].sum())
        p_intent = float(sub_p["purchase_intent_score"].mean()) if p_cnt > 0 else 0.0
        print(f" {method:<14} | {p_cnt:>7,} | INR {p_risk:>14,.2f} | INR {p_exp:>16,.2f} | {p_intent:>7.1f}")
    print("-" * 70)

    # Top 10 Highest-Value Recovery Opportunities
    print("\n Top 10 Highest-Value Recovery Opportunities:")
    print("-" * 70)
    top_10 = abandoned_df.sort_values(by=["expected_recoverable_revenue", "risk_score"], ascending=False).head(10)
    print(f" {'Event ID':<12} | {'Customer ID':<12} | {'Cart Value':<12} | {'Intent':<7} | {'Risk':<6} | {'Priority':<9} | {'Expected Recov.'}")
    print("-" * 70)
    for _, row in top_10.iterrows():
        print(
            f" {row['event_id']:<12} | {row['customer_id']:<12} | INR {row['cart_value']:>8,.2f} | "
            f"{row['purchase_intent_score']:>5.1f} | {row['risk_score']:>5.1f} | {row['priority']:<9} | INR {row['expected_recoverable_revenue']:>10,.2f}"
        )
    print("=" * 70 + "\n")

    # Optionally persist evaluated dataset
    evaluated_df.to_csv(paths["enriched_path"], index=False)
    print(f"[OK] Full risk-evaluated dataset saved to: {paths['enriched_path']}\n")

    return {
        "total_events": total_events,
        "abandoned_events": len(abandoned_df),
        "recovery_candidates": len(candidates_df),
        "potential_revenue_at_risk_inr": round(total_at_risk, 2),
        "expected_recoverable_revenue_inr": round(total_expected_recoverable, 2),
        "recovery_potential_pct": round(efficiency_pct, 2),
        "tier_metrics": tier_metrics,
    }


if __name__ == "__main__":
    run_portfolio_risk_evaluation()
