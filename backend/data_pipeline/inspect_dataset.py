"""
Dataset Inspection Script for RecoverAI
Inspects raw e-commerce session data and prints a structured banner report.
"""

import os
import sys
import pandas as pd


def get_raw_dataset_path() -> str:
    """Find and return the absolute path to raw dataset."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
    raw_path = os.path.join(root_dir, "data", "raw", "indian_ecommerce.csv")
    return raw_path


def inspect_dataset(file_path: str = None) -> dict:
    """
    Load and inspect the dataset without assuming predefined schema.
    Returns a dictionary of inspection summary metrics.
    """
    if file_path is None:
        file_path = get_raw_dataset_path()

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Raw dataset not found at '{file_path}'. "
            f"Please ensure 'indian_ecommerce.csv' is placed in 'data/raw/'."
        )

    df = pd.read_csv(file_path)

    # Basic shape & duplicates
    total_rows, total_cols = df.shape
    dup_count = int(df.duplicated().sum())

    # Missing values
    null_counts = df.isnull().sum().to_dict()
    total_nulls = int(df.isnull().sum().sum())

    # Inspect columns dynamically
    columns_info = {col: str(df[col].dtype) for col in df.columns}

    # Customer & Session metrics (if present)
    cust_col = next((c for c in df.columns if "customer" in c.lower()), None)
    sess_col = next((c for c in df.columns if "session" in c.lower() or "transaction" in c.lower()), None)
    pay_col = next((c for c in df.columns if "payment" in c.lower()), None)
    purch_col = next((c for c in df.columns if "purchas" in c.lower()), None)
    cart_col = next((c for c in df.columns if "cart" in c.lower()), None)

    unique_customers = int(df[cust_col].nunique()) if cust_col else 0
    unique_sessions = int(df[sess_col].nunique()) if sess_col else 0
    payment_methods = df[pay_col].value_counts().to_dict() if pay_col else {}
    purchase_counts = df[purch_col].value_counts().to_dict() if purch_col else {}
    cart_counts = df[cart_col].value_counts().to_dict() if cart_col else {}

    report = {
        "file_path": file_path,
        "rows": total_rows,
        "columns_count": total_cols,
        "column_names": list(df.columns),
        "dtypes": columns_info,
        "total_nulls": total_nulls,
        "null_counts": null_counts,
        "duplicate_rows": dup_count,
        "unique_customers": unique_customers,
        "unique_sessions": unique_sessions,
        "payment_methods": payment_methods,
        "purchase_counts": purchase_counts,
        "cart_counts": cart_counts,
    }

    # Banner print
    print("=" * 60)
    print(" RecoverAI Dataset Inspection Report")
    print("=" * 60)
    print(f" Source File       : {os.path.basename(file_path)}")
    print(f" Dataset Shape     : {total_rows:,} rows × {total_cols} columns")
    print(f" Duplicate Rows    : {dup_count:,}")
    print(f" Total Null Values : {total_nulls:,}")
    print(f" Unique Customers  : {unique_customers:,}")
    print(f" Unique Sessions   : {unique_sessions:,}")
    print("-" * 60)
    print(" Columns & Data Types:")
    for col, dtype in columns_info.items():
        nulls = null_counts.get(col, 0)
        null_str = f"({nulls} nulls)" if nulls > 0 else "(no nulls)"
        print(f"   - {col:<26}: {dtype:<10} {null_str}")
    print("-" * 60)
    if pay_col:
        print(f" Payment Method Distribution ({pay_col}):")
        for method, cnt in payment_methods.items():
            pct = (cnt / total_rows) * 100
            print(f"   - Method {method:<10}: {cnt:>6,} ({pct:>5.1f}%)")
    print("-" * 60)
    if purch_col:
        print(f" Purchase Status Distribution ({purch_col}):")
        for status, cnt in purchase_counts.items():
            pct = (cnt / total_rows) * 100
            print(f"   - Status {status:<10}: {cnt:>6,} ({pct:>5.1f}%)")
    print("=" * 60)

    return report


if __name__ == "__main__":
    inspect_dataset()
