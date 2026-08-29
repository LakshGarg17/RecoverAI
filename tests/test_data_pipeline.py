"""
Unit and integration tests for RecoverAI Data Pipeline (Day 2)
Tests dataset inspection, cleaning, transformation, intent scoring, and canonical schema.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

# Ensure backend and data_pipeline are importable
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
pipeline_dir = os.path.join(root_dir, "backend", "data_pipeline")
for p in [root_dir, pipeline_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from inspect_dataset import inspect_dataset, get_raw_dataset_path
from clean_dataset import clean_ecommerce_dataset
from transform_dataset import (
    compute_customer_aggregates,
    calculate_purchase_intent_score,
    transform_to_canonical_schema,
    PAYMENT_METHOD_MAP,
)
from run_pipeline import generate_representative_sample, get_pipeline_paths


def test_raw_dataset_exists_and_inspectable():
    """Verify raw dataset is present in data/raw/ and inspectable."""
    raw_path = get_raw_dataset_path()
    assert os.path.exists(raw_path), f"Raw dataset not found at {raw_path}"

    report = inspect_dataset(raw_path)
    assert report["rows"] == 25000
    assert report["columns_count"] == 29
    assert report["unique_customers"] == 8442
    assert report["unique_sessions"] == 25000
    assert report["duplicate_rows"] == 0


def test_clean_dataset_imputation_and_types():
    """Verify cleaning handles nulls, formats dates, and bounds numeric values."""
    mock_data = pd.DataFrame({
        "customer_id": [1, 2],
        "session_id": [101, 102],
        "visit_date": ["15-03-2024", "invalid-date"],
        "unit_price": [-50.0, np.nan],
        "quantity": [0, 2],
        "discount_percent": [10, 0],
        "discount_amount": [100.0, 0.0],
        "revenue": [500.0, 0.0],
        "pages_viewed": [0, 15],
        "time_on_site_sec": [-10, 500],
        "added_to_cart": [1, 0],
        "purchased": [1, 0],
        "cart_abandoned": [0, 0],
        "payment_method": [0, 1],
    })

    cleaned = clean_ecommerce_dataset(mock_data)
    assert not cleaned.isnull().values.any()
    assert (cleaned["unit_price"] >= 0.0).all()
    assert (cleaned["quantity"] >= 1).all()
    assert (cleaned["pages_viewed"] >= 1).all()
    assert (cleaned["time_on_site_sec"] >= 0).all()


def test_customer_aggregates_computation():
    """Verify customer level aggregate features are correctly aggregated."""
    mock_df = pd.DataFrame({
        "customer_id": [1, 1, 2],
        "session_id": [101, 102, 103],
        "purchased": [1, 0, 1],
        "cart_abandoned": [0, 1, 0],
        "revenue": [1500.0, 0.0, 2000.0],
    })

    agg = compute_customer_aggregates(mock_df)
    assert 1 in agg.index
    assert 2 in agg.index
    assert agg.loc[1, "total_sessions"] == 2
    assert agg.loc[1, "successful_purchases"] == 1
    assert agg.loc[1, "abandoned_carts"] == 1
    assert agg.loc[1, "total_spend"] == 1500.0
    assert agg.loc[1, "average_order_value"] == 1500.0


def test_purchase_intent_score_calibration():
    """Verify intent score is bounded strictly [0, 100] and reflects engagement."""
    # Archetype 1: High engagement repeat buyer
    score_high = calculate_purchase_intent_score(
        pages_viewed=pd.Series([22]),
        session_duration=pd.Series([1600]),
        added_to_cart=pd.Series([1]),
        cart_value=pd.Series([3500.0]),
        total_sessions=pd.Series([5]),
        successful_purchases=pd.Series([3]),
        customer_ltv=pd.Series([5000.0]),
    ).iloc[0]

    # Archetype 2: First-time window shopper (no cart)
    score_low = calculate_purchase_intent_score(
        pages_viewed=pd.Series([2]),
        session_duration=pd.Series([60]),
        added_to_cart=pd.Series([0]),
        cart_value=pd.Series([0.0]),
        total_sessions=pd.Series([1]),
        successful_purchases=pd.Series([0]),
        customer_ltv=pd.Series([0.0]),
    ).iloc[0]

    assert 0.0 <= score_high <= 100.0
    assert 0.0 <= score_low <= 100.0
    assert score_high > 90.0, f"High archetype score expected > 90, got {score_high}"
    assert score_low < 15.0, f"Low archetype score expected < 15, got {score_low}"


def test_canonical_schema_transformation():
    """Verify transformation to canonical RecoverAI schema and revenue at risk logic."""
    raw_path = get_raw_dataset_path()
    raw_df = pd.read_csv(raw_path).head(500)
    clean_df = clean_ecommerce_dataset(raw_df)
    events_df, cust_df = transform_to_canonical_schema(clean_df)

    expected_cols = [
        "event_id", "customer_id", "session_id", "amount", "currency",
        "payment_method", "event_type", "purchase_status", "cart_value",
        "session_duration", "pages_viewed", "purchase_history",
        "customer_lifetime_value", "purchase_intent_score", "revenue_at_risk",
        "risk_score", "recovery_probability", "recommended_action"
    ]

    for col in expected_cols:
        assert col in events_df.columns, f"Missing canonical column '{col}'"

    # ID format checks
    assert events_df["event_id"].iloc[0].startswith("evt_")
    assert events_df["customer_id"].iloc[0].startswith("cust_")
    assert events_df["session_id"].iloc[0].startswith("sess_")
    assert (events_df["currency"] == "INR").all()

    # Revenue at risk validation:
    # Only abandoned carts have positive revenue_at_risk
    abandoned_subset = events_df[events_df["event_type"] == "cart_abandoned"]
    completed_subset = events_df[events_df["event_type"] == "purchase_completed"]
    browse_subset = events_df[events_df["event_type"] == "page_browse"]

    assert (abandoned_subset["revenue_at_risk"] == abandoned_subset["cart_value"]).all()
    assert (completed_subset["revenue_at_risk"] == 0.0).all()
    assert (browse_subset["revenue_at_risk"] == 0.0).all()


def test_representative_sample_generation():
    """Verify generated sample contains exactly 100 rows across diverse event types."""
    paths = get_pipeline_paths()
    sample_path = paths["sample_path"]
    assert os.path.exists(sample_path), f"Sample file not found at {sample_path}"

    sample_df = pd.read_csv(sample_path)
    assert len(sample_df) == 100
    assert "cart_abandoned" in sample_df["event_type"].values
    assert "purchase_completed" in sample_df["event_type"].values
    assert "page_browse" in sample_df["event_type"].values
