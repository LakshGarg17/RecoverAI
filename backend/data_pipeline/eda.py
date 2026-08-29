"""
Exploratory Data Analysis (EDA) Script for RecoverAI
Analyzes customer behavior, checkout funnel, payment distribution, and revenue at risk.
"""

import os
import json
import pandas as pd
import numpy as np


def run_eda(raw_path: str = None) -> dict:
    """Run programmatic EDA on the e-commerce dataset."""
    if raw_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
        raw_path = os.path.join(root_dir, "data", "raw", "indian_ecommerce.csv")

    df = pd.read_csv(raw_path)

    # Derived fields for analysis
    df["calculated_cart_val"] = (df["unit_price"] * df["quantity"]) - df["discount_amount"]
    df["calculated_cart_val"] = df["calculated_cart_val"].clip(lower=0.0)

    # 1. Customer Behavior
    total_sessions = len(df)
    unique_custs = df["customer_id"].nunique()
    sessions_per_cust = df.groupby("customer_id")["session_id"].count()
    repeat_custs = (sessions_per_cust > 1).sum()
    pct_repeat_custs = (repeat_custs / unique_custs) * 100

    # Customer lifetime metrics from dataset
    completed_df = df[df["purchased"] == 1]
    cust_spend = completed_df.groupby("customer_id")["revenue"].sum()
    cust_purchases = completed_df.groupby("customer_id")["session_id"].count()

    total_revenue = float(completed_df["revenue"].sum())
    aov = float(completed_df["revenue"].mean()) if len(completed_df) > 0 else 0.0
    median_order_val = float(completed_df["revenue"].median()) if len(completed_df) > 0 else 0.0

    # 2. Checkout & Cart Behavior
    cart_added_sessions = int((df["added_to_cart"] == 1).sum())
    abandoned_sessions = int((df["cart_abandoned"] == 1).sum())
    completed_sessions = int((df["purchased"] == 1).sum())
    browse_only_sessions = int((df["added_to_cart"] == 0).sum())

    cart_abandonment_rate = (abandoned_sessions / cart_added_sessions * 100) if cart_added_sessions > 0 else 0.0
    purchase_completion_rate = (completed_sessions / total_sessions * 100)

    # Engagement comparisons
    engagement_stats = {
        "overall": {
            "avg_duration_sec": float(df["time_on_site_sec"].mean()),
            "median_duration_sec": float(df["time_on_site_sec"].median()),
            "avg_pages_viewed": float(df["pages_viewed"].mean()),
            "median_pages_viewed": float(df["pages_viewed"].median()),
        },
        "abandoned": {
            "avg_duration_sec": float(df[df["cart_abandoned"] == 1]["time_on_site_sec"].mean()),
            "median_duration_sec": float(df[df["cart_abandoned"] == 1]["time_on_site_sec"].median()),
            "avg_pages_viewed": float(df[df["cart_abandoned"] == 1]["pages_viewed"].mean()),
            "median_pages_viewed": float(df[df["cart_abandoned"] == 1]["pages_viewed"].median()),
        },
        "completed": {
            "avg_duration_sec": float(df[df["purchased"] == 1]["time_on_site_sec"].mean()),
            "median_duration_sec": float(df[df["purchased"] == 1]["time_on_site_sec"].median()),
            "avg_pages_viewed": float(df[df["purchased"] == 1]["pages_viewed"].mean()),
            "median_pages_viewed": float(df[df["purchased"] == 1]["pages_viewed"].median()),
        },
        "browse_only": {
            "avg_duration_sec": float(df[df["added_to_cart"] == 0]["time_on_site_sec"].mean()),
            "median_duration_sec": float(df[df["added_to_cart"] == 0]["time_on_site_sec"].median()),
            "avg_pages_viewed": float(df[df["added_to_cart"] == 0]["pages_viewed"].mean()),
            "median_pages_viewed": float(df[df["added_to_cart"] == 0]["pages_viewed"].median()),
        }
    }

    # 3. Revenue Metrics & Potential Revenue at Risk
    abandoned_df = df[df["cart_abandoned"] == 1]
    potential_revenue_at_risk = float(abandoned_df["calculated_cart_val"].sum())
    avg_revenue_at_risk_per_cart = float(abandoned_df["calculated_cart_val"].mean()) if len(abandoned_df) > 0 else 0.0

    # 4. Payment Methods
    payment_map = {
        0: "UPI",
        1: "CARD",
        2: "DEBIT_CARD",
        3: "NETBANKING",
        4: "WALLET",
        5: "COD_EMI"
    }

    df["payment_method_label"] = df["payment_method"].map(payment_map).fillna("UNKNOWN")
    pay_summary = []
    for code, label in payment_map.items():
        sub = df[df["payment_method"] == code]
        sub_completed = sub[sub["purchased"] == 1]
        sub_abandoned = sub[sub["cart_abandoned"] == 1]
        total_p = len(sub)
        pay_summary.append({
            "code": code,
            "label": label,
            "total_attempts": total_p,
            "share_pct": round((total_p / total_sessions) * 100, 2),
            "completed": len(sub_completed),
            "completed_rate_pct": round((len(sub_completed) / total_p) * 100, 2) if total_p > 0 else 0.0,
            "abandoned": len(sub_abandoned),
            "revenue_completed": round(float(sub_completed["revenue"].sum()), 2),
            "revenue_at_risk": round(float(sub_abandoned["calculated_cart_val"].sum()), 2),
        })

    eda_results = {
        "total_records": total_sessions,
        "unique_customers": unique_custs,
        "repeat_customers": int(repeat_custs),
        "repeat_customers_pct": round(pct_repeat_custs, 2),
        "cart_added_sessions": cart_added_sessions,
        "completed_sessions": completed_sessions,
        "abandoned_sessions": abandoned_sessions,
        "browse_only_sessions": browse_only_sessions,
        "cart_abandonment_rate_pct": round(cart_abandonment_rate, 2),
        "purchase_completion_rate_pct": round(purchase_completion_rate, 2),
        "total_completed_revenue_inr": round(total_revenue, 2),
        "aov_inr": round(aov, 2),
        "median_order_value_inr": round(median_order_val, 2),
        "potential_revenue_at_risk_inr": round(potential_revenue_at_risk, 2),
        "avg_revenue_at_risk_per_cart_inr": round(avg_revenue_at_risk_per_cart, 2),
        "engagement_stats": engagement_stats,
        "payment_summary": pay_summary,
    }

    print("============================================================")
    print(" RecoverAI Exploratory Data Analysis Summary")
    print("============================================================")
    print(f" Total Sessions Analyzed      : {total_sessions:,}")
    print(f" Unique Customers             : {unique_custs:,}")
    print(f" Repeat Customers             : {repeat_custs:,} ({pct_repeat_custs:.1f}%)")
    print(f" Cart Creation Events         : {cart_added_sessions:,} ({(cart_added_sessions/total_sessions)*100:.1f}%)")
    print(f" Completed Purchases          : {completed_sessions:,} ({purchase_completion_rate:.1f}%)")
    print(f" Abandoned Carts              : {abandoned_sessions:,} ({cart_abandonment_rate:.1f}% of created carts)")
    print("-" * 60)
    print(f" Total Completed Revenue      : INR {total_revenue:,.2f}")
    print(f" Average Order Value (AOV)    : INR {aov:,.2f}")
    print(f" POTENTIAL REVENUE AT RISK    : INR {potential_revenue_at_risk:,.2f}")
    print(f" Avg At-Risk Value per Cart   : INR {avg_revenue_at_risk_per_cart:,.2f}")
    print("============================================================")

    return eda_results


if __name__ == "__main__":
    run_eda()
