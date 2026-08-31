"""
RecoverAI Deterministic Revenue Risk Engine (Day 3)
Evaluates customer events to identify high-value payment recovery opportunities.
Calculates Expected Recoverable Revenue, blended multi-factor risk scores, and priority tiers.
"""

from typing import Dict, Any, Union, Optional
import math
import numpy as np
import pandas as pd


# Scoring Weights
WEIGHT_CART_VALUE = 0.25      # 25%
WEIGHT_PURCHASE_INTENT = 0.30 # 30%
WEIGHT_CUSTOMER_HISTORY = 0.20# 20%
WEIGHT_ENGAGEMENT = 0.15      # 15%
WEIGHT_RECENCY = 0.10         # 10%

# Benchmarks for Normalization
CART_VALUE_BENCHMARK_INR = 3500.0
CLV_BENCHMARK_INR = 4000.0
PURCHASE_COUNT_BENCHMARK = 3.0
SESSION_COUNT_BENCHMARK = 5.0
SESSION_DURATION_BENCHMARK_SEC = 1500.0
PAGES_VIEWED_BENCHMARK = 20.0


def compute_cart_value_score(cart_value: float) -> float:
    """
    Computes normalized cart/order value score (0-100).
    Higher monetary value in cart translates to higher recovery impact.
    """
    if cart_value is None or math.isnan(cart_value) or cart_value <= 0:
        return 0.0
    normalized = min(float(cart_value) / CART_VALUE_BENCHMARK_INR, 1.0) * 100.0
    return round(float(np.clip(normalized, 0.0, 100.0)), 2)


def compute_customer_history_score(
    purchase_history: int,
    customer_lifetime_value: float,
    total_sessions: Optional[int] = None
) -> float:
    """
    Computes customer loyalty and repeat purchasing score (0-100).
    A repeat customer abandoning a high-value cart scores higher than a first-time visitor.
    """
    p_hist = max(0, int(purchase_history or 0))
    clv = max(0.0, float(customer_lifetime_value or 0.0))

    # Factor 1: Prior completed orders (0 to 45 pts)
    score_orders = min(p_hist / PURCHASE_COUNT_BENCHMARK, 1.0) * 45.0

    # Factor 2: Historical spend / CLV (0 to 35 pts)
    score_clv = min(clv / CLV_BENCHMARK_INR, 1.0) * 35.0

    # Factor 3: Loyalty frequency (0 to 20 pts)
    if total_sessions is not None and total_sessions > 0:
        score_freq = min(float(total_sessions) / SESSION_COUNT_BENCHMARK, 1.0) * 20.0
    else:
        # Default bonus if repeat purchaser
        score_freq = 20.0 if p_hist >= 1 else 5.0

    total = score_orders + score_clv + score_freq
    return round(float(np.clip(total, 0.0, 100.0)), 2)


def compute_engagement_score(
    session_duration: int,
    pages_viewed: int,
    has_cart: bool = True
) -> float:
    """
    Computes active browsing and checkout exploration score (0-100).
    """
    duration = max(0, int(session_duration or 0))
    pages = max(1, int(pages_viewed or 1))

    # Duration factor (0 to 45 pts)
    score_duration = min(duration / SESSION_DURATION_BENCHMARK_SEC, 1.0) * 45.0

    # Pages factor (0 to 35 pts)
    score_pages = min(pages / PAGES_VIEWED_BENCHMARK, 1.0) * 35.0

    # Cart action flag (0 or 20 pts)
    score_cart = 20.0 if has_cart else 0.0

    total = score_duration + score_pages + score_cart
    return round(float(np.clip(total, 0.0, 100.0)), 2)


def compute_recency_score(
    recency_hours: Optional[float] = None,
    timestamp: Any = None
) -> float:
    """
    Computes time-decay recency score (0-100):
    < 1 hour    -> 100
    1-6 hours   -> 80
    6-24 hours  -> 60
    1-3 days    -> 30
    > 3 days    -> 10
    """
    hours = recency_hours

    if hours is None and timestamp is not None:
        try:
            ts = pd.to_datetime(timestamp)
            now = pd.Timestamp.now()
            diff_hours = (now - ts).total_seconds() / 3600.0
            hours = max(0.0, diff_hours)
        except Exception:
            hours = None

    if hours is None or math.isnan(hours):
        # Default for active recovery queue simulation
        return 80.0

    if hours < 1.0:
        return 100.0
    elif hours < 6.0:
        return 80.0
    elif hours < 24.0:
        return 60.0
    elif hours <= 72.0:
        return 30.0
    else:
        return 10.0


def classify_priority(risk_score: float) -> str:
    """
    Categorizes blended risk score into operational priority tiers:
    80-100 -> CRITICAL
    60-79  -> HIGH
    40-59  -> MEDIUM
    0-39   -> LOW
    """
    if risk_score >= 80.0:
        return "CRITICAL"
    elif risk_score >= 60.0:
        return "HIGH"
    elif risk_score >= 40.0:
        return "MEDIUM"
    else:
        return "LOW"


def compute_expected_recoverable_revenue(
    cart_value: float,
    purchase_intent_score: float
) -> float:
    """
    Computes Expected Recoverable Revenue:
    Expected Recoverable Revenue = cart_value * purchase_intent_probability
    (purchase_intent_probability = purchase_intent_score / 100)
    """
    if cart_value is None or math.isnan(cart_value) or cart_value <= 0:
        return 0.0
    intent_prob = np.clip(float(purchase_intent_score or 0.0) / 100.0, 0.0, 1.0)
    return round(float(cart_value * intent_prob), 2)


def evaluate_event_risk(event: Union[Dict[str, Any], pd.Series]) -> Dict[str, Any]:
    """
    Evaluates a single RecoverAI event.
    Returns a structured evaluation containing Expected Recoverable Revenue,
    blended risk score, priority tier, and score breakdown.
    """
    # Normalize inputs
    if hasattr(event, "to_dict"):
        event_dict = event.to_dict()
    elif isinstance(event, dict):
        event_dict = event
    else:
        event_dict = dict(event)

    event_id = str(event_dict.get("event_id", "evt_unknown"))
    customer_id = str(event_dict.get("customer_id", "cust_unknown"))
    event_type = str(event_dict.get("event_type", "cart_abandoned"))
    purchase_status = str(event_dict.get("purchase_status", "abandoned"))

    cart_value = float(event_dict.get("cart_value", 0.0) or 0.0)
    revenue_at_risk = float(event_dict.get("revenue_at_risk", 0.0) or 0.0)
    # If revenue_at_risk wasn't passed directly, derive from cart_value if abandoned
    if revenue_at_risk <= 0.0 and event_type == "cart_abandoned":
        revenue_at_risk = cart_value

    session_duration = int(event_dict.get("session_duration", 0) or 0)
    pages_viewed = int(event_dict.get("pages_viewed", 1) or 1)
    purchase_history = int(event_dict.get("purchase_history", 0) or 0)
    customer_lifetime_value = float(event_dict.get("customer_lifetime_value", 0.0) or 0.0)
    total_sessions = event_dict.get("total_sessions")

    # Purchase Intent Score
    intent_score = event_dict.get("purchase_intent_score")
    if intent_score is None or (isinstance(intent_score, float) and math.isnan(intent_score)):
        # Fallback calculation if missing
        intent_score = 50.0
    else:
        intent_score = float(intent_score)

    recency_hours = event_dict.get("recency_hours")
    timestamp = event_dict.get("timestamp") or event_dict.get("visit_date")

    # 1. Component Sub-scores (each 0 - 100)
    cart_val_score = compute_cart_value_score(cart_value)
    intent_score_val = round(float(np.clip(intent_score, 0.0, 100.0)), 2)
    history_score = compute_customer_history_score(
        purchase_history=purchase_history,
        customer_lifetime_value=customer_lifetime_value,
        total_sessions=total_sessions
    )
    engagement_score = compute_engagement_score(
        session_duration=session_duration,
        pages_viewed=pages_viewed,
        has_cart=(cart_value > 0 or event_type == "cart_abandoned")
    )
    recency_score = compute_recency_score(
        recency_hours=recency_hours,
        timestamp=timestamp
    )

    # 2. Deterministic Blended Risk Score (0 - 100)
    blended_score = (
        (WEIGHT_CART_VALUE * cart_val_score) +
        (WEIGHT_PURCHASE_INTENT * intent_score_val) +
        (WEIGHT_CUSTOMER_HISTORY * history_score) +
        (WEIGHT_ENGAGEMENT * engagement_score) +
        (WEIGHT_RECENCY * recency_score)
    )
    risk_score = round(float(np.clip(blended_score, 0.0, 100.0)), 2)

    # 3. Urgency Priority Tier
    priority = classify_priority(risk_score)

    # 4. Expected Recoverable Revenue
    if event_type == "cart_abandoned" or revenue_at_risk > 0:
        expected_recoverable = compute_expected_recoverable_revenue(cart_value, intent_score_val)
    else:
        expected_recoverable = 0.0

    # 5. Recovery Candidate Qualification
    is_abandoned = (event_type == "cart_abandoned" or purchase_status == "abandoned" or revenue_at_risk > 0)
    is_candidate = bool(is_abandoned and cart_value > 0 and risk_score >= 30.0)

    return {
        "event_id": event_id,
        "customer_id": customer_id,
        "revenue_at_risk": round(revenue_at_risk, 2),
        "expected_recoverable_revenue": round(expected_recoverable, 2),
        "risk_score": risk_score,
        "priority": priority,
        "recovery_candidate": is_candidate,
        "score_breakdown": {
            "cart_value_score": cart_val_score,
            "purchase_intent_score": intent_score_val,
            "customer_history_score": history_score,
            "engagement_score": engagement_score,
            "recency_score": recency_score,
        }
    }


def batch_evaluate_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs deterministic risk engine across an entire DataFrame of events.
    Appends risk_score, priority, expected_recoverable_revenue, and recovery_candidate.
    """
    df = df.copy()

    # Pre-allocate result columns
    risk_scores = []
    priorities = []
    expected_revenues = []
    recovery_candidates = []
    cart_scores = []
    history_scores = []
    engagement_scores = []
    recency_scores = []

    for _, row in df.iterrows():
        res = evaluate_event_risk(row)
        risk_scores.append(res["risk_score"])
        priorities.append(res["priority"])
        expected_revenues.append(res["expected_recoverable_revenue"])
        recovery_candidates.append(res["recovery_candidate"])
        cart_scores.append(res["score_breakdown"]["cart_value_score"])
        history_scores.append(res["score_breakdown"]["customer_history_score"])
        engagement_scores.append(res["score_breakdown"]["engagement_score"])
        recency_scores.append(res["score_breakdown"]["recency_score"])

    df["risk_score"] = risk_scores
    df["priority"] = priorities
    df["expected_recoverable_revenue"] = expected_revenues
    df["recovery_candidate"] = recovery_candidates
    df["score_cart_value"] = cart_scores
    df["score_customer_history"] = history_scores
    df["score_engagement"] = engagement_scores
    df["score_recency"] = recency_scores

    return df
