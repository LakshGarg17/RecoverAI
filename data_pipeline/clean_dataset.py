"""
Dataset Cleaning and Standardization Module for RecoverAI
Applies column-appropriate imputation, type validation, and timestamp normalization.
"""

import os
import pandas as pd
import numpy as np


def clean_ecommerce_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw e-commerce DataFrame:
    1. Defensive missing value handling (median for numeric, category-appropriate for categorical)
    2. Datetime standardization
    3. Monotonic price/quantity validation
    4. Type casting
    """
    df = df.copy()

    # 1. Date normalization
    if "visit_date" in df.columns:
        # Expected format in dataset: DD-MM-YYYY
        df["visit_date"] = pd.to_datetime(df["visit_date"], format="%d-%m-%Y", errors="coerce")
        # In case of missing/invalid dates, forward/backward fill or drop
        df["visit_date"] = df["visit_date"].fillna(pd.Timestamp("2024-01-01"))
    else:
        df["visit_date"] = pd.Timestamp("2024-01-01")

    # 2. Numeric columns validation & imputation
    numeric_columns = {
        "customer_id": int,
        "session_id": int,
        "device_type": int,
        "user_type": int,
        "marketing_channel": int,
        "product_id": int,
        "product_category": int,
        "unit_price": float,
        "quantity": int,
        "discount_percent": float,
        "discount_amount": float,
        "revenue": float,
        "pages_viewed": int,
        "time_on_site_sec": int,
        "added_to_cart": int,
        "purchased": int,
        "cart_abandoned": int,
        "rating": float,
        "review_text": int,
        "review_helpful_votes": int,
        "payment_method": int,
        "location": int,
    }

    for col, target_type in numeric_columns.items():
        if col in df.columns:
            if target_type == float:
                if df[col].isnull().any():
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                df[col] = df[col].astype(float)
            elif target_type == int:
                if df[col].isnull().any():
                    mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else 0
                    df[col] = df[col].fillna(mode_val)
                df[col] = df[col].astype(int)

    # 3. Categorical columns imputation
    categorical_columns = ["session_duration_bucket"]
    for col in categorical_columns:
        if col in df.columns:
            df[col] = df[col].fillna("unknown").astype(str)

    # 4. Consistency checks & sanity bounds
    # Ensure quantity >= 1
    if "quantity" in df.columns:
        df["quantity"] = df["quantity"].clip(lower=1)

    # Ensure unit_price >= 0.0
    if "unit_price" in df.columns:
        df["unit_price"] = df["unit_price"].clip(lower=0.0)

    # Ensure discount_amount is non-negative and <= unit_price * quantity
    if "discount_amount" in df.columns and "unit_price" in df.columns and "quantity" in df.columns:
        gross_val = df["unit_price"] * df["quantity"]
        df["discount_amount"] = df["discount_amount"].clip(lower=0.0)
        df["discount_amount"] = np.minimum(df["discount_amount"], gross_val)

    # Ensure pages_viewed >= 1 and time_on_site_sec >= 0
    if "pages_viewed" in df.columns:
        df["pages_viewed"] = df["pages_viewed"].clip(lower=1)
    if "time_on_site_sec" in df.columns:
        df["time_on_site_sec"] = df["time_on_site_sec"].clip(lower=0)

    # Ensure binary indicators are 0 or 1
    for binary_col in ["added_to_cart", "purchased", "cart_abandoned"]:
        if binary_col in df.columns:
            df[binary_col] = df[binary_col].apply(lambda x: 1 if x == 1 else 0)

    return df


if __name__ == "__main__":
    from inspect_dataset import get_raw_dataset_path
    raw_path = get_raw_dataset_path()
    raw_df = pd.read_csv(raw_path)
    clean_df = clean_ecommerce_dataset(raw_df)
    print(f"Dataset successfully cleaned. Shape: {clean_df.shape}")
