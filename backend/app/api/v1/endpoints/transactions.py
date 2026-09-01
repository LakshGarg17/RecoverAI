"""
Transactions Endpoint (Day 8)
Provides paginated list of transaction logs and recovery execution records.
"""

from typing import Dict, Any, Optional
import os
import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from database.execution_models import RecoveryExecution
from database.recovery_models import RecoveryRecord

router = APIRouter()

def _get_project_root() -> str:
    current = os.path.abspath(os.path.dirname(__file__))
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, "data")):
            return current
        current = os.path.dirname(current)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

ROOT_DIR = _get_project_root()
PROCESSED_DATA_PATH = os.path.join(ROOT_DIR, "data", "processed", "recoverai_events.csv")
SAMPLE_DATA_PATH = os.path.join(ROOT_DIR, "data", "samples", "recoverai_sample.csv")



@router.get("", summary="List Transactions & Recovery Executions")
def list_transactions_endpoint(
    page: int = 1,
    limit: int = 15,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns transactions list with filtering by status and search terms.
    """
    executions = db.query(RecoveryExecution).all()
    recoveries = db.query(RecoveryRecord).all()
    rec_by_exec = {r.execution_id: r for r in recoveries}

    items = []
    
    # Add real DB recovery executions
    for ex in executions:
        rec = rec_by_exec.get(ex.execution_id)
        
        tx_status = ex.status
        if rec and rec.status == "RECOVERED":
            tx_status = "RECOVERED"
        elif ex.status == "SUCCEEDED":
            tx_status = "RECOVERED"
        elif ex.status in ["CREATED", "EXECUTING"]:
            tx_status = "PENDING"
        elif ex.status in ["FAILED", "REJECTED", "EXPIRED"]:
            tx_status = "FAILED"

        items.append({
            "transaction_id": ex.execution_id,
            "event_id": ex.event_id,
            "customer_id": ex.customer_id,
            "amount": ex.amount,
            "currency": ex.currency,
            "payment_link_id": ex.payment_link_id or "—",
            "payment_id": rec.payment_id if rec else (ex.provider_reference or "—"),
            "provider": ex.provider,
            "status": tx_status,
            "action": ex.action,
            "created_at": ex.created_at.isoformat() if ex.created_at else "2026-08-31T12:00:00Z",
        })

    # If DB executions are few, enrich from sample transactions
    if len(items) < 30:
        df = pd.DataFrame()
        for p in [PROCESSED_DATA_PATH, SAMPLE_DATA_PATH]:
            if os.path.exists(p):
                try:
                    df = pd.read_csv(p)
                    break
                except Exception:
                    continue

        if not df.empty:
            for idx, row in df.head(50).iterrows():
                ev_id = str(row.get("event_id"))
                if any(it["event_id"] == ev_id for it in items):
                    continue
                
                raw_st = str(row.get("purchase_status", "abandoned")).lower()
                if raw_st == "completed":
                    st = "RECOVERED"
                elif raw_st == "abandoned":
                    st = "PENDING"
                else:
                    st = "FAILED"

                items.append({
                    "transaction_id": f"txn_{ev_id}",
                    "event_id": ev_id,
                    "customer_id": str(row.get("customer_id")),
                    "amount": float(row.get("cart_value") or 1500.0),
                    "currency": "INR",
                    "payment_link_id": f"plink_sample_{ev_id[-6:]}" if st != "FAILED" else "—",
                    "payment_id": f"pay_rzp_{ev_id[-6:]}" if st == "RECOVERED" else "—",
                    "provider": "razorpay (Test Mode)",
                    "status": st,
                    "action": "PAYMENT_LINK" if float(row.get("cart_value") or 0) > 3000 else "PERSONALIZED_REMINDER",
                    "created_at": str(row.get("timestamp") or "2026-08-31T12:00:00Z"),
                })

    # Filtering
    filtered = []
    for it in items:
        if status and status.upper() != "ALL":
            if it["status"].upper() != status.upper():
                continue
        if search:
            s = search.lower()
            if (s not in it["transaction_id"].lower() and
                s not in it["customer_id"].lower() and
                s not in it["event_id"].lower() and
                s not in str(it.get("payment_id", "")).lower()):
                continue
        filtered.append(it)

    total = len(filtered)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_items = filtered[start_idx:end_idx]
    total_pages = max(1, (total + limit - 1) // limit)

    return {
        "items": paginated_items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }
