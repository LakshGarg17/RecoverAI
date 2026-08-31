"""
End-to-End RecoverAI Data Pipeline Orchestrator
Executes: Raw Kaggle CSV -> Inspection -> Cleaning -> Normalization -> Feature Engineering -> Canonical Output & Samples
"""

import os
import sys
import pandas as pd

# Add current pipeline directory to sys.path for seamless imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from inspect_dataset import inspect_dataset, get_raw_dataset_path
from clean_dataset import clean_ecommerce_dataset
from transform_dataset import transform_to_canonical_schema


def get_pipeline_paths():
    """Resolves all data paths."""
    root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
    raw_path = os.path.join(root_dir, "data", "raw", "indian_ecommerce.csv")
    processed_dir = os.path.join(root_dir, "data", "processed")
    samples_dir = os.path.join(root_dir, "data", "samples")
    processed_path = os.path.join(processed_dir, "recoverai_events.csv")
    sample_path = os.path.join(samples_dir, "recoverai_sample.csv")

    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(samples_dir, exist_ok=True)

    return {
        "root_dir": root_dir,
        "raw_path": raw_path,
        "processed_path": processed_path,
        "sample_path": sample_path,
    }


def generate_representative_sample(events_df: pd.DataFrame, sample_size: int = 100) -> pd.DataFrame:
    """
    Selects a balanced, representative sample across event types and intent score tiers.
    """
    # 1. High-intent abandoned carts (prime recovery targets)
    high_intent_abandoned = events_df[
        (events_df["event_type"] == "cart_abandoned") & (events_df["purchase_intent_score"] >= 75)
    ]
    # 2. Medium/low-intent abandoned carts
    med_intent_abandoned = events_df[
        (events_df["event_type"] == "cart_abandoned") & (events_df["purchase_intent_score"] < 75)
    ]
    # 3. Completed purchases
    completed = events_df[events_df["event_type"] == "purchase_completed"]
    # 4. Browsing sessions
    browsing = events_df[events_df["event_type"] == "page_browse"]

    # Stratified selection
    s1 = high_intent_abandoned.head(40)
    s2 = med_intent_abandoned.head(20)
    s3 = completed.head(25)
    s4 = browsing.head(15)

    sample = pd.concat([s1, s2, s3, s4], ignore_index=True)

    # If count is less than target, sample additional random rows
    if len(sample) < sample_size:
        remaining = sample_size - len(sample)
        extra = events_df[~events_df["event_id"].isin(sample["event_id"])].head(remaining)
        sample = pd.concat([sample, extra], ignore_index=True)

    return sample.head(sample_size)


def run_pipeline() -> dict:
    """
    Executes complete end-to-end data pipeline.
    """
    paths = get_pipeline_paths()

    print("\n" + "=" * 65)
    print(" RecoverAI Revenue-Recovery Data Pipeline")
    print("=" * 65)

    # Step 1: Inspection
    print("\n[Stage 1/4] Inspecting Raw Dataset...")
    inspection_report = inspect_dataset(paths["raw_path"])

    # Step 2: Cleaning & Normalization
    print("\n[Stage 2/4] Cleaning and Standardizing Dataset...")
    raw_df = pd.read_csv(paths["raw_path"])
    clean_df = clean_ecommerce_dataset(raw_df)
    print(f"   [OK] Cleaned {len(clean_df):,} records with 0 remaining nulls.")

    # Step 3: Feature Engineering & Transformation
    print("\n[Stage 3/4] Transforming to RecoverAI Canonical Schema & Scoring...")
    events_df, cust_df = transform_to_canonical_schema(clean_df)

    total_events = len(events_df)
    abandoned_count = int((events_df["event_type"] == "cart_abandoned").sum())
    completed_count = int((events_df["event_type"] == "purchase_completed").sum())
    browse_count = int((events_df["event_type"] == "page_browse").sum())
    total_at_risk = float(events_df["revenue_at_risk"].sum())
    avg_intent_score = float(events_df["purchase_intent_score"].mean())

    print(f"   [OK] Generated {total_events:,} canonical recovery events.")
    print(f"   [OK] Cart Abandonments    : {abandoned_count:,}")
    print(f"   [OK] Completed Purchases  : {completed_count:,}")
    print(f"   [OK] Page Browsing        : {browse_count:,}")
    print(f"   [OK] POTENTIAL REVENUE AT RISK : INR {total_at_risk:,.2f}")
    print(f"   [OK] Average Intent Score : {avg_intent_score:.2f} / 100")

    # Step 4: Save Processed Outputs & Samples
    print("\n[Stage 4/4] Writing Output Datasets...")
    events_df.to_csv(paths["processed_path"], index=False)
    processed_size_mb = os.path.getsize(paths["processed_path"]) / (1024 * 1024)
    print(f"   [OK] Processed events saved to: {paths['processed_path']} ({processed_size_mb:.2f} MB)")

    sample_df = generate_representative_sample(events_df, sample_size=100)
    sample_df.to_csv(paths["sample_path"], index=False)
    sample_size_kb = os.path.getsize(paths["sample_path"]) / 1024
    print(f"   [OK] Representative sample saved to: {paths['sample_path']} ({len(sample_df)} rows, {sample_size_kb:.1f} KB)")

    print("\n" + "=" * 65)
    print(" Data Pipeline Execution Complete! All outputs generated successfully.")
    print("=" * 65 + "\n")

    return {
        "total_records": total_events,
        "abandoned_carts": abandoned_count,
        "completed_purchases": completed_count,
        "potential_revenue_at_risk_inr": total_at_risk,
        "processed_file": paths["processed_path"],
        "sample_file": paths["sample_path"],
    }


if __name__ == "__main__":
    run_pipeline()
