"""
Proxy / Direct module exposing RecoverAI Risk Engine at backend.services.risk_engine
"""

import os
import sys

# Ensure backend root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.risk_engine import (
    evaluate_event_risk,
    batch_evaluate_events,
    compute_cart_value_score,
    compute_customer_history_score,
    compute_engagement_score,
    compute_recency_score,
    classify_priority,
    compute_expected_recoverable_revenue,
    WEIGHT_CART_VALUE,
    WEIGHT_PURCHASE_INTENT,
    WEIGHT_CUSTOMER_HISTORY,
    WEIGHT_ENGAGEMENT,
    WEIGHT_RECENCY,
)

__all__ = [
    "evaluate_event_risk",
    "batch_evaluate_events",
    "compute_cart_value_score",
    "compute_customer_history_score",
    "compute_engagement_score",
    "compute_recency_score",
    "classify_priority",
    "compute_expected_recoverable_revenue",
    "WEIGHT_CART_VALUE",
    "WEIGHT_PURCHASE_INTENT",
    "WEIGHT_CUSTOMER_HISTORY",
    "WEIGHT_ENGAGEMENT",
    "WEIGHT_RECENCY",
]
