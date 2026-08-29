"""
AI Diagnosis and Recovery Recommendation Agent (Day 4)
Orchestrates context building, LLM structured calls, strict validation, and deterministic fallbacks.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union

# Ensure root & backend paths are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.join(root_dir, "backend")
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ai.schemas import (
    DiagnosisCategory,
    RecoveryAction,
    PriorityTier,
    AIDiagnosisResult,
    AIDecisionContext,
    DiagnoseEventResponse,
)
from ai.prompts import SYSTEM_PROMPT, build_diagnosis_user_prompt
from backend.app.core.config import settings
from backend.app.services.risk_engine import evaluate_event_risk

logger = logging.getLogger(__name__)

# Cache processed dataset in memory for fast event lookups
_CACHED_PROCESSED_DF: Optional[pd.DataFrame] = None


def get_processed_dataset() -> pd.DataFrame:
    """Loads and caches data/processed/recoverai_events.csv."""
    global _CACHED_PROCESSED_DF
    if _CACHED_PROCESSED_DF is None:
        processed_path = os.path.join(root_dir, "data", "processed", "recoverai_events.csv")
        if os.path.exists(processed_path):
            _CACHED_PROCESSED_DF = pd.read_csv(processed_path)
        else:
            # Fallback to sample if full processed not yet generated
            sample_path = os.path.join(root_dir, "data", "samples", "recoverai_sample.csv")
            if os.path.exists(sample_path):
                _CACHED_PROCESSED_DF = pd.read_csv(sample_path)
            else:
                _CACHED_PROCESSED_DF = pd.DataFrame()
    return _CACHED_PROCESSED_DF


def build_ai_decision_context(
    event_data: Union[Dict[str, Any], pd.Series, str],
    df: Optional[pd.DataFrame] = None
) -> AIDecisionContext:
    """
    Assembles a comprehensive context object from event telemetry,
    customer historical metrics (Day 2), and deterministic risk engine outputs (Day 3).
    """
    if isinstance(event_data, str):
        # Treat as event_id lookup
        dataset = df if df is not None else get_processed_dataset()
        matched = dataset[dataset["event_id"] == event_data]
        if matched.empty:
            raise ValueError(f"Event ID '{event_data}' not found in processed dataset.")
        raw_dict = matched.iloc[0].to_dict()
    elif hasattr(event_data, "to_dict"):
        raw_dict = event_data.to_dict()
    elif isinstance(event_data, dict):
        raw_dict = dict(event_data)
    else:
        raise TypeError(f"Unsupported event_data type: {type(event_data)}")

    # 1. Run Day 3 Deterministic Risk Engine to ensure all scores are authoritative
    risk_output = evaluate_event_risk(raw_dict)

    cart_value = float(raw_dict.get("cart_value", raw_dict.get("amount", 0.0)) or 0.0)
    session_duration = int(raw_dict.get("session_duration", raw_dict.get("time_on_site_sec", 0)) or 0)
    pages_viewed = int(raw_dict.get("pages_viewed", 1) or 1)
    prev_purchases = int(raw_dict.get("purchase_history", 0) or 0)
    clv = float(raw_dict.get("customer_lifetime_value", 0.0) or 0.0)
    total_sessions = int(raw_dict.get("total_sessions", 1) or 1)
    aov = float(raw_dict.get("average_order_value", (clv / prev_purchases) if prev_purchases > 0 else 0.0) or 0.0)
    abandonment_rate = float(raw_dict.get("cart_abandonment_rate", 0.0) or 0.0)

    context = AIDecisionContext(
        event_id=str(raw_dict.get("event_id", "evt_unknown")),
        customer_id=str(raw_dict.get("customer_id", "cust_unknown")),
        session_id=str(raw_dict.get("session_id", "sess_unknown")),
        cart_value=round(cart_value, 2),
        currency=str(raw_dict.get("currency", "INR")),
        payment_method=str(raw_dict.get("payment_method", "UPI")),
        session_duration=session_duration,
        pages_viewed=pages_viewed,
        purchase_status=str(raw_dict.get("purchase_status", "abandoned")),
        previous_purchases=prev_purchases,
        customer_lifetime_value=round(clv, 2),
        average_order_value=round(aov, 2),
        cart_abandonment_rate=round(abandonment_rate, 2),
        total_sessions=total_sessions,
        risk_score=float(risk_output["risk_score"]),
        priority=str(risk_output["priority"]),
        purchase_intent_score=float(risk_output["score_breakdown"]["purchase_intent_score"]),
        revenue_at_risk=float(risk_output["revenue_at_risk"]),
        expected_recoverable_revenue=float(risk_output["expected_recoverable_revenue"]),
    )
    return context


def generate_deterministic_fallback(
    context: AIDecisionContext,
    failure_reason: str = "Fallback triggered"
) -> AIDiagnosisResult:
    """
    Deterministic rule-based fallback when LLM API is unavailable, times out,
    or produces invalid outputs. Ensures 100% system availability.
    """
    logger.info(f"Generating deterministic fallback for {context.event_id} ({failure_reason})")

    # Case 1: No active cart or non-abandoned event
    if context.cart_value <= 0.0 or context.purchase_status != "abandoned":
        return AIDiagnosisResult(
            diagnosis=DiagnosisCategory.LOW_INTENT_ABANDONMENT,
            recovery_probability=0.05,
            recommended_action=RecoveryAction.NO_ACTION,
            priority=PriorityTier.LOW,
            recommendation_confidence=0.95,
            reason_codes=["zero_cart_value", "no_action_required", "deterministic_fallback"],
            explanation="No monetary cart value or active checkout session detected. Outreach not recommended.",
            suggested_message="",
        )

    # Case 2: CRITICAL priority (risk_score >= 80)
    if context.risk_score >= 80.0 or context.priority == "CRITICAL":
        if context.previous_purchases >= 1:
            return AIDiagnosisResult(
                diagnosis=DiagnosisCategory.REPEAT_CUSTOMER_ABANDONMENT,
                recovery_probability=round(min(0.90, max(0.75, context.purchase_intent_score / 100.0)), 2),
                recommended_action=RecoveryAction.PERSONALIZED_REMINDER,
                priority=PriorityTier.CRITICAL,
                recommendation_confidence=0.92,
                reason_codes=["critical_risk", "repeat_customer", "high_clv", "deterministic_fallback"],
                explanation=(
                    f"Valued repeat buyer ({context.customer_id}) with {context.previous_purchases} prior order(s) "
                    f"and ₹{context.customer_lifetime_value:,.2f} lifetime spend abandoned cart worth ₹{context.cart_value:,.2f}. "
                    f"High urgency personalized reminder recommended."
                ),
                suggested_message=(
                    f"Hi there! We noticed you left your selected items (₹{context.cart_value:,.2f}) in your cart. "
                    f"As a valued customer, click here to complete your checkout with 1-click!"
                ),
            )
        else:
            return AIDiagnosisResult(
                diagnosis=DiagnosisCategory.HIGH_VALUE_ABANDONMENT,
                recovery_probability=round(min(0.85, max(0.70, context.purchase_intent_score / 100.0)), 2),
                recommended_action=RecoveryAction.PAYMENT_LINK,
                priority=PriorityTier.CRITICAL,
                recommendation_confidence=0.85,
                reason_codes=["critical_risk", "high_cart_value", "payment_link_recommended", "deterministic_fallback"],
                explanation=(
                    f"High cart value (₹{context.cart_value:,.2f}) with strong engagement ({context.pages_viewed} pages). "
                    f"Direct payment link recommended to remove checkout friction."
                ),
                suggested_message=(
                    f"Complete your order of ₹{context.cart_value:,.2f} seamlessly using your secure instant checkout link here."
                ),
            )

    # Case 3: HIGH priority (60 <= risk_score < 80)
    if context.risk_score >= 60.0 or context.priority == "HIGH":
        return AIDiagnosisResult(
            diagnosis=DiagnosisCategory.HIGH_PURCHASE_INTENT_ABANDONMENT,
            recovery_probability=round(min(0.75, max(0.55, context.purchase_intent_score / 100.0)), 2),
            recommended_action=RecoveryAction.CHECKOUT_REMINDER,
            priority=PriorityTier.HIGH,
            recommendation_confidence=0.88,
            reason_codes=["high_intent", "strong_engagement", "checkout_reminder", "deterministic_fallback"],
            explanation=(
                f"High purchase intent ({context.purchase_intent_score:.1f}/100) and substantial session exploration "
                f"({round(context.session_duration/60, 1)} min). Standard checkout reminder recommended."
            ),
            suggested_message=(
                f"You left items in your cart! Complete your purchase today to secure your order."
            ),
        )

    # Case 4: MEDIUM priority (40 <= risk_score < 60)
    if context.risk_score >= 40.0 or context.priority == "MEDIUM":
        return AIDiagnosisResult(
            diagnosis=DiagnosisCategory.RECENT_CHECKOUT_DROP,
            recovery_probability=round(min(0.50, max(0.35, context.purchase_intent_score / 100.0)), 2),
            recommended_action=RecoveryAction.DELAYED_FOLLOW_UP,
            priority=PriorityTier.MEDIUM,
            recommendation_confidence=0.80,
            reason_codes=["moderate_intent", "delayed_follow_up", "deterministic_fallback"],
            explanation=(
                f"Moderate engagement detected. Recommending a delayed follow-up to give buyer space before re-engaging."
            ),
            suggested_message=(
                f"Still thinking it over? Your cart is saved and ready whenever you want to complete your order."
            ),
        )

    # Case 5: LOW priority (risk_score < 40)
    return AIDiagnosisResult(
        diagnosis=DiagnosisCategory.LOW_INTENT_ABANDONMENT,
        recovery_probability=round(min(0.30, max(0.10, context.purchase_intent_score / 100.0)), 2),
        recommended_action=RecoveryAction.NO_ACTION,
        priority=PriorityTier.LOW,
        recommendation_confidence=0.90,
        reason_codes=["low_risk_score", "low_intent", "no_action_needed", "deterministic_fallback"],
        explanation="Low engagement and low intent score. No autonomous outreach recommended to prevent customer spam.",
        suggested_message="",
    )


class AIDiagnosisAgent:
    """
    RecoverAI LLM Diagnosis Agent service.
    Translates deterministic risk metrics into root cause diagnosis,
    recovery probability, and structured recommendations.
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL

    def is_configured(self) -> bool:
        """Check if a real non-placeholder OpenAI key is configured."""
        return (
            bool(self.api_key)
            and not self.api_key.startswith("sk-placeholder")
            and len(self.api_key) > 10
        )

    async def diagnose_event(
        self,
        event_data: Union[Dict[str, Any], pd.Series, str],
        force_fallback: bool = False
    ) -> DiagnoseEventResponse:
        """
        Diagnoses a single event, calls LLM or fallback, validates output,
        computes expected_recovery_value, and returns a structured response.
        """
        # 1. Build rich Context Object
        context = build_ai_decision_context(event_data)

        # 2. If fallback forced or OpenAI not configured, use deterministic fallback
        if force_fallback or not self.is_configured():
            fallback_res = generate_deterministic_fallback(
                context,
                failure_reason="Force fallback mode" if force_fallback else "OpenAI API key not configured"
            )
            expected_val = round(context.revenue_at_risk * fallback_res.recovery_probability, 2)
            return DiagnoseEventResponse(
                event_id=context.event_id,
                customer_id=context.customer_id,
                diagnosis=fallback_res.diagnosis,
                recovery_probability=fallback_res.recovery_probability,
                expected_recovery_value=expected_val,
                revenue_at_risk=context.revenue_at_risk,
                recommended_action=fallback_res.recommended_action,
                priority=fallback_res.priority,
                recommendation_confidence=fallback_res.recommendation_confidence,
                reason_codes=fallback_res.reason_codes,
                explanation=fallback_res.explanation,
                suggested_message=fallback_res.suggested_message,
                source="fallback",
                model_name=None,
            )

        # 3. Invoke OpenAI with Structured Outputs
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        user_prompt = build_diagnosis_user_prompt(context)

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            raw_content = response.choices[0].message.content or "{}"
            raw_json = json.loads(raw_content)

            # Strict Pydantic Validation of LLM Output
            validated_result = AIDiagnosisResult.model_validate(raw_json)
            expected_val = round(context.revenue_at_risk * validated_result.recovery_probability, 2)

            return DiagnoseEventResponse(
                event_id=context.event_id,
                customer_id=context.customer_id,
                diagnosis=validated_result.diagnosis,
                recovery_probability=validated_result.recovery_probability,
                expected_recovery_value=expected_val,
                revenue_at_risk=context.revenue_at_risk,
                recommended_action=validated_result.recommended_action,
                priority=validated_result.priority,
                recommendation_confidence=validated_result.recommendation_confidence,
                reason_codes=validated_result.reason_codes,
                explanation=validated_result.explanation,
                suggested_message=validated_result.suggested_message,
                source="ai",
                model_name=self.model,
            )
        except Exception as e:
            logger.warning(f"AI diagnosis LLM call failed for {context.event_id}: {e}. Engaging deterministic fallback.")
            fallback_res = generate_deterministic_fallback(context, failure_reason=str(e))
            expected_val = round(context.revenue_at_risk * fallback_res.recovery_probability, 2)
            return DiagnoseEventResponse(
                event_id=context.event_id,
                customer_id=context.customer_id,
                diagnosis=fallback_res.diagnosis,
                recovery_probability=fallback_res.recovery_probability,
                expected_recovery_value=expected_val,
                revenue_at_risk=context.revenue_at_risk,
                recommended_action=fallback_res.recommended_action,
                priority=fallback_res.priority,
                recommendation_confidence=fallback_res.recommendation_confidence,
                reason_codes=fallback_res.reason_codes,
                explanation=fallback_res.explanation,
                suggested_message=fallback_res.suggested_message,
                source="fallback",
                model_name=self.model,
            )


# Global singleton instance
ai_diagnosis_agent = AIDiagnosisAgent()

__all__ = [
    "AIDiagnosisAgent",
    "ai_diagnosis_agent",
    "build_ai_decision_context",
    "generate_deterministic_fallback",
    "get_processed_dataset",
]
