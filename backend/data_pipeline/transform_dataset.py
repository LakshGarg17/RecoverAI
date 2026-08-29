"""
Transformation and Feature Engineering Module for RecoverAI
Transforms cleaned e-commerce records into canonical RecoverAI recovery events schema.
"""

import os
import pandas as pd
import numpy as np


PAYMENT_METHOD_MAP = {
    0: "UPI",
    1: "CARD",
    2: "DEBIT_CARD",
    3: "NETBANKING",
    4: "WALLET",
    5: "COD_EMI",
}


def compute_customer_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes customer-level historical aggregate metrics across all sessions.
    Returns a DataFrame indexed by customer_id with aggregated features.
    """
    # Group by customer_id
    grouped = df.groupby("customer_id")

    # Aggregate base metrics
    total_sessions = grouped["session_id"].count().rename("total_sessions")
    successful_purchases = grouped["purchased"].apply(lambda x: (x == 1).sum()).rename("successful_purchases")
    abandoned_carts = grouped["cart_abandoned"].apply(lambda x: (x == 1).sum()).rename("abandoned_carts")

    # Spend metrics (only for completed purchases)
    spend_series = df[df["purchased"] == 1].groupby("customer_id")["revenue"].sum().rename("total_spend")

    cust_summary = pd.DataFrame({
        "total_sessions": total_sessions,
        "successful_purchases": successful_purchases,
        "abandoned_carts": abandoned_carts,
    })

    cust_summary["total_spend"] = cust_summary.index.map(spend_series).fillna(0.0).round(2)
    cust_summary["average_order_value"] = np.where(
        cust_summary["successful_purchases"] > 0,
        (cust_summary["total_spend"] / cust_summary["successful_purchases"]).round(2),
        0.0
    )
    total_cart_actions = cust_summary["successful_purchases"] + cust_summary["abandoned_carts"]
    cust_summary["cart_abandonment_rate"] = np.where(
        total_cart_actions > 0,
        ((cust_summary["abandoned_carts"] / total_cart_actions) * 100.0).round(2),
        0.0
    )
    cust_summary["purchase_frequency"] = np.where(
        cust_summary["total_sessions"] > 0,
        (cust_summary["successful_purchases"] / cust_summary["total_sessions"]).round(3),
        0.0
    )

    return cust_summary


def calculate_purchase_intent_score(
    pages_viewed: pd.Series,
    session_duration: pd.Series,
    added_to_cart: pd.Series,
    cart_value: pd.Series,
    total_sessions: pd.Series,
    successful_purchases: pd.Series,
    customer_ltv: pd.Series,
) -> pd.Series:
    """
    Calculates observable Purchase Intent Score (0 to 100).
    Components:
    - Engagement (30 pts): Pages viewed (15 pts) + Session duration (15 pts)
    - Action Intent (35 pts): Add-to-cart flag (25 pts) + Cart monetary value intensity (10 pts)
    - Customer Loyalty (35 pts): Session count (10 pts) + Purchase history (15 pts) + Lifetime Spend (10 pts)
    """
    # 1. Engagement (0-30)
    score_pages = np.minimum(pages_viewed / 20.0, 1.0) * 15.0
    score_duration = np.minimum(session_duration / 1500.0, 1.0) * 15.0

    # 2. Action Intent (0-35)
    score_cart_added = np.where(added_to_cart == 1, 25.0, 0.0)
    score_cart_val = np.where(added_to_cart == 1, np.minimum(cart_value / 3000.0, 1.0) * 10.0, 0.0)

    # 3. Customer Profile & Loyalty (0-35)
    score_sessions = np.minimum(total_sessions / 5.0, 1.0) * 10.0
    score_purchases = np.minimum(successful_purchases / 3.0, 1.0) * 15.0
    score_ltv = np.minimum(customer_ltv / 4000.0, 1.0) * 10.0

    total_score = (
        score_pages
        + score_duration
        + score_cart_added
        + score_cart_val
        + score_sessions
        + score_purchases
        + score_ltv
    )

    # Clamp strictly between 0.0 and 100.0 and round
    return total_score.clip(lower=0.0, upper=100.0).round(2)


def transform_to_canonical_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms cleaned e-commerce DataFrame into canonical RecoverAI recovery events schema.
    """
    # 1. Compute customer aggregates
    cust_aggregates = compute_customer_aggregates(df)

    # Merge customer aggregate metrics back to session level
    merged = df.merge(
        cust_aggregates,
        left_on="customer_id",
        right_index=True,
        how="left"
    )

    # 2. Calculate cart value
    raw_cart_val = (merged["unit_price"] * merged["quantity"]) - merged["discount_amount"]
    merged["cart_value"] = np.where(
        merged["added_to_cart"] == 1,
        raw_cart_val.clip(lower=0.0).round(2),
        0.0
    )

    # 3. Classify event_type, purchase_status, amount, and potential revenue_at_risk
    # Event types: cart_abandoned, purchase_completed, page_browse
    # Purchase statuses: abandoned, completed, browsing
    conditions = [
        (merged["purchased"] == 1),
        (merged["cart_abandoned"] == 1),
        (merged["added_to_cart"] == 0),
    ]

    event_types = ["purchase_completed", "cart_abandoned", "page_browse"]
    purchase_statuses = ["completed", "abandoned", "browsing"]

    merged["event_type"] = np.select(conditions, event_types, default="page_browse")
    merged["purchase_status"] = np.select(conditions, purchase_statuses, default="browsing")

    # Transaction/Event Amount
    merged["amount"] = np.where(
        merged["purchased"] == 1,
        merged["revenue"].round(2),
        merged["cart_value"].round(2)
    )

    # Potential Revenue at Risk: Only non-zero for abandoned carts
    merged["revenue_at_risk"] = np.where(
        merged["cart_abandoned"] == 1,
        merged["cart_value"].round(2),
        0.0
    )

    # 4. Calculate Purchase Intent Score
    merged["purchase_intent_score"] = calculate_purchase_intent_score(
        pages_viewed=merged["pages_viewed"],
        session_duration=merged["time_on_site_sec"],
        added_to_cart=merged["added_to_cart"],
        cart_value=merged["cart_value"],
        total_sessions=merged["total_sessions"],
        successful_purchases=merged["successful_purchases"],
        customer_ltv=merged["total_spend"],
    )

    # 5. Canonical formatting & IDs
    canonical_df = pd.DataFrame()
    canonical_df["event_id"] = merged["session_id"].apply(lambda sid: f"evt_{sid:06d}")
    canonical_df["customer_id"] = merged["customer_id"].apply(lambda cid: f"cust_{cid:05d}")
    canonical_df["session_id"] = merged["session_id"].apply(lambda sid: f"sess_{sid:06d}")
    canonical_df["amount"] = merged["amount"]
    canonical_df["currency"] = "INR"
    canonical_df["payment_method"] = merged["payment_method"].map(PAYMENT_METHOD_MAP).fillna("UPI")
    canonical_df["event_type"] = merged["event_type"]
    canonical_df["purchase_status"] = merged["purchase_status"]
    canonical_df["cart_value"] = merged["cart_value"]
    canonical_df["session_duration"] = merged["time_on_site_sec"]
    canonical_df["pages_viewed"] = merged["pages_viewed"]
    canonical_df["purchase_history"] = merged["successful_purchases"]
    canonical_df["customer_lifetime_value"] = merged["total_spend"]
    canonical_df["purchase_intent_score"] = merged["purchase_intent_score"]
    canonical_df["revenue_at_risk"] = merged["revenue_at_risk"]

    # Reserved fields for Day 3 / Day 4 risk engine & strategy engine
    canonical_df["risk_score"] = np.nan
    canonical_df["recovery_probability"] = np.nan
    canonical_df["recommended_action"] = ""

    return canonical_df, cust_aggregates


if __name__ == "__main__":
    from inspect_dataset import get_raw_dataset_path
    from clean_dataset import clean_ecommerce_dataset

    raw_path = get_raw_dataset_path()
    raw_df = pd.read_csv(raw_path)
    clean_df = clean_ecommerce_dataset(raw_df)
    events_df, cust_df = transform_to_canonical_schema(clean_df)

    print("Canonical Transformation Complete:")
    print(f"Events Shape: {events_df.shape}")
    print(f"Unique Customers: {cust_df.shape[0]}")
    print("\nSample Transformed Events:")
    print(events_df.head(5)[["event_id", "customer_id", "event_type", "amount", "purchase_intent_score", "revenue_at_risk"]])
