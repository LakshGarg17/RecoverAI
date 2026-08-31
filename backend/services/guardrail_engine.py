"""
RecoverAI Guardrail Engine & Risk Controls (Day 6)
Executes deterministic validation checks on Decision Engine recommendations before any recovery action.
States: IDENTIFIED -> ANALYZED -> RECOMMENDED -> GUARDRAIL_PENDING -> APPROVED -> READY_FOR_EXECUTION
Branch states: BLOCKED, REVIEW_REQUIRED
"""

import os
import sys
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy.orm import Session

# Ensure root & backend paths are on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ai.schemas import (
    RecoveryAction,
    AIDecisionContext,
    GuardrailStatus,
    ExecutionState,
    CheckStatus,
    GuardrailCheckDetail,
    GuardrailValidationResult,
)
from backend.config.recovery_policy import RecoveryPolicy, DEFAULT_RECOVERY_POLICY, get_recovery_policy
from backend.services.decision_engine import DecisionResult, decision_engine_service
from database.decision_models import RecoveryDecision, get_recovery_decision_by_event_id
from database.audit_models import (
    GuardrailAuditLog,
    save_guardrail_audit_log,
    get_audit_log_by_idempotency_key,
    get_audit_logs_by_customer_id,
    get_recent_audit_logs_for_event,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Individual Modular Guardrail Checks
# ============================================================================

def check_purchase_completion(
    purchase_status: Optional[str],
    purchase_completed: Optional[bool] = None
) -> GuardrailCheckDetail:
    """
    Check 1: Real-time Purchase Completion Check.
    If transaction/cart is already completed/successful, block recovery intervention immediately.
    Fail-closed: if purchase_status is completely unknown/None, block or flag for review.
    """
    if purchase_status is None and purchase_completed is None:
        return GuardrailCheckDetail(
            name="purchase_completion",
            status=CheckStatus.FAILED,
            message="Real-time payment status is unverified / unavailable (fail-closed).",
            value_observed="UNKNOWN",
            threshold_applied="Status must be 'abandoned' or 'pending'",
        )

    norm_status = str(purchase_status).strip().lower() if purchase_status else ""
    is_completed = (
        purchase_completed is True
        or norm_status in ("completed", "success", "successful", "recovered", "paid")
    )

    if is_completed:
        return GuardrailCheckDetail(
            name="purchase_completion",
            status=CheckStatus.FAILED,
            message="Purchase already completed. Recovery outreach blocked.",
            value_observed=norm_status or "completed",
            threshold_applied="Status must not be completed/success",
        )

    if norm_status not in ("abandoned", "pending", "failed"):
        return GuardrailCheckDetail(
            name="purchase_completion",
            status=CheckStatus.FAILED,
            message=f"Purchase status '{norm_status}' is not eligible for autonomous recovery.",
            value_observed=norm_status,
            threshold_applied="abandoned, pending, failed",
        )

    return GuardrailCheckDetail(
        name="purchase_completion",
        status=CheckStatus.PASSED,
        message=f"Purchase status verified as '{norm_status}' (not completed).",
        value_observed=norm_status,
        threshold_applied="not completed",
    )


def check_risk_threshold(
    risk_score: Optional[float],
    policy: RecoveryPolicy
) -> GuardrailCheckDetail:
    """
    Check 2: Risk Score Threshold Check.
    Requires risk_score >= policy.minimum_risk_score.
    """
    if risk_score is None:
        return GuardrailCheckDetail(
            name="risk_threshold",
            status=CheckStatus.FAILED,
            message="Risk score is missing or uncalculated (fail-closed).",
            value_observed=None,
            threshold_applied=f">={policy.minimum_risk_score}",
        )

    if risk_score < policy.minimum_risk_score:
        return GuardrailCheckDetail(
            name="risk_threshold",
            status=CheckStatus.FAILED,
            message=f"Risk score ({risk_score:.1f}) below merchant threshold ({policy.minimum_risk_score:.1f}).",
            value_observed=round(risk_score, 1),
            threshold_applied=policy.minimum_risk_score,
        )

    return GuardrailCheckDetail(
        name="risk_threshold",
        status=CheckStatus.PASSED,
        message=f"Risk score ({risk_score:.1f}) satisfies threshold (>={policy.minimum_risk_score:.1f}).",
        value_observed=round(risk_score, 1),
        threshold_applied=policy.minimum_risk_score,
    )


def check_recovery_probability(
    recovery_probability: Optional[float],
    policy: RecoveryPolicy
) -> GuardrailCheckDetail:
    """
    Check 3: Recovery Probability Threshold Check.
    Requires recovery_probability >= policy.minimum_recovery_probability.
    """
    if recovery_probability is None:
        return GuardrailCheckDetail(
            name="recovery_probability",
            status=CheckStatus.FAILED,
            message="Recovery probability is missing or undefined (fail-closed).",
            value_observed=None,
            threshold_applied=f">={policy.minimum_recovery_probability*100:.0f}%",
        )

    if recovery_probability < policy.minimum_recovery_probability:
        return GuardrailCheckDetail(
            name="recovery_probability",
            status=CheckStatus.FAILED,
            message=f"Recovery probability ({recovery_probability*100:.1f}%) below merchant threshold ({policy.minimum_recovery_probability*100:.1f}%).",
            value_observed=round(recovery_probability, 2),
            threshold_applied=policy.minimum_recovery_probability,
        )

    return GuardrailCheckDetail(
        name="recovery_probability",
        status=CheckStatus.PASSED,
        message=f"Recovery probability ({recovery_probability*100:.1f}%) satisfies minimum ({policy.minimum_recovery_probability*100:.1f}%).",
        value_observed=round(recovery_probability, 2),
        threshold_applied=policy.minimum_recovery_probability,
    )


def check_expected_recovery_value(
    expected_recovery_value: Optional[float],
    policy: RecoveryPolicy
) -> GuardrailCheckDetail:
    """
    Check 4: Expected Recovery Value Threshold Check.
    Requires expected_recovery_value >= policy.minimum_expected_value.
    """
    if expected_recovery_value is None:
        return GuardrailCheckDetail(
            name="expected_recovery_value",
            status=CheckStatus.FAILED,
            message="Expected recovery value is missing or undefined (fail-closed).",
            value_observed=None,
            threshold_applied=f">= ₹{policy.minimum_expected_value:.2f}",
        )

    if expected_recovery_value < policy.minimum_expected_value:
        return GuardrailCheckDetail(
            name="expected_recovery_value",
            status=CheckStatus.FAILED,
            message=f"Expected recovery value (₹{expected_recovery_value:,.2f}) below merchant threshold (₹{policy.minimum_expected_value:,.2f}).",
            value_observed=round(expected_recovery_value, 2),
            threshold_applied=policy.minimum_expected_value,
        )

    return GuardrailCheckDetail(
        name="expected_recovery_value",
        status=CheckStatus.PASSED,
        message=f"Expected recovery value (₹{expected_recovery_value:,.2f}) meets minimum requirement (₹{policy.minimum_expected_value:,.2f}).",
        value_observed=round(expected_recovery_value, 2),
        threshold_applied=policy.minimum_expected_value,
    )


def check_max_attempts(
    recovery_attempt_count: int,
    policy: RecoveryPolicy
) -> GuardrailCheckDetail:
    """
    Check 5: Maximum Recovery Attempts Check.
    Requires recovery_attempt_count < policy.max_recovery_attempts.
    """
    max_allowed = policy.max_recovery_attempts or policy.max_contact_attempts

    if recovery_attempt_count >= max_allowed:
        return GuardrailCheckDetail(
            name="max_attempts",
            status=CheckStatus.FAILED,
            message=f"Maximum recovery attempts reached ({recovery_attempt_count}/{max_allowed}).",
            value_observed=recovery_attempt_count,
            threshold_applied=max_allowed,
        )

    return GuardrailCheckDetail(
        name="max_attempts",
        status=CheckStatus.PASSED,
        message=f"Attempt count ({recovery_attempt_count}/{max_allowed}) is within allowable limit.",
        value_observed=recovery_attempt_count,
        threshold_applied=max_allowed,
    )


def check_cooldown_window(
    minutes_since_last_attempt: Optional[float],
    policy: RecoveryPolicy
) -> GuardrailCheckDetail:
    """
    Check 6: Cooldown Quiet Time Window Check.
    Requires time since last attempt >= policy.cooldown_minutes (if prior attempt exists).
    """
    if minutes_since_last_attempt is None:
        # First attempt (no prior attempt recorded)
        return GuardrailCheckDetail(
            name="cooldown_window",
            status=CheckStatus.PASSED,
            message="No prior recovery attempts recorded; cooldown satisfied.",
            value_observed=None,
            threshold_applied=f"{policy.cooldown_minutes}m",
        )

    if minutes_since_last_attempt < policy.cooldown_minutes:
        return GuardrailCheckDetail(
            name="cooldown_window",
            status=CheckStatus.FAILED,
            message=(
                f"Cooldown active: last attempt was {int(minutes_since_last_attempt)} minutes ago "
                f"(cooldown required: {policy.cooldown_minutes}m)."
            ),
            value_observed=round(minutes_since_last_attempt, 1),
            threshold_applied=policy.cooldown_minutes,
        )

    return GuardrailCheckDetail(
        name="cooldown_window",
        status=CheckStatus.PASSED,
        message=f"Cooldown window satisfied ({int(minutes_since_last_attempt)}m >= {policy.cooldown_minutes}m).",
        value_observed=round(minutes_since_last_attempt, 1),
        threshold_applied=policy.cooldown_minutes,
    )



def check_duplicate_action(
    event_id: str,
    action: RecoveryAction,
    recent_event_audit_logs: Optional[List[Any]] = None
) -> GuardrailCheckDetail:
    """
    Check 7: Duplicate Action Prevention Check.
    Detects if the same action was recently generated/approved for this specific event.
    """
    act_str = action.value if hasattr(action, "value") else str(action)
    
    if recent_event_audit_logs:
        for log in recent_event_audit_logs:
            # If an approved or ready_for_execution log for the same event and action exists in the last 2 hours
            log_action = getattr(log, "final_action", None) or getattr(log, "requested_action", None)
            log_status = getattr(log, "status", None)
            if log_action == act_str and log_status in ("APPROVED", "READY_FOR_EXECUTION"):
                return GuardrailCheckDetail(
                    name="duplicate_action_prevention",
                    status=CheckStatus.FAILED,
                    message=f"Duplicate recovery action '{act_str}' recently generated for event '{event_id}'.",
                    value_observed=act_str,
                    threshold_applied="Unique action per active recovery cycle",
                )

    return GuardrailCheckDetail(
        name="duplicate_action_prevention",
        status=CheckStatus.PASSED,
        message=f"No duplicate pending/approved '{act_str}' action detected for event '{event_id}'.",
        value_observed=act_str,
        threshold_applied="Unique action per active recovery cycle",
    )


def check_action_permission(
    action: RecoveryAction,
    policy: RecoveryPolicy
) -> GuardrailCheckDetail:
    """
    Check 8: Merchant Action Permission Policy Check.
    Enforces merchant configuration flags (allow_payment_link, allow_personalized_reminder, etc.).
    """
    act_str = action.value if hasattr(action, "value") else str(action)

    if action == RecoveryAction.PAYMENT_LINK:
        allowed = bool(policy.allow_payment_link and policy.allow_payment_links)
        policy_flag = "allow_payment_link"
    elif action == RecoveryAction.PERSONALIZED_REMINDER:
        allowed = bool(policy.allow_personalized_reminder and policy.allow_personalized_messages)
        policy_flag = "allow_personalized_reminder"
    elif action == RecoveryAction.CHECKOUT_REMINDER:
        allowed = bool(policy.allow_checkout_reminder)
        policy_flag = "allow_checkout_reminder"
    elif action == RecoveryAction.DELAYED_FOLLOW_UP:
        allowed = bool(policy.allow_delayed_follow_up)
        policy_flag = "allow_delayed_follow_up"
    elif action == RecoveryAction.NO_ACTION:
        allowed = True
        policy_flag = "always_allowed"
    else:
        allowed = False
        policy_flag = "unknown_action"

    if not allowed:
        return GuardrailCheckDetail(
            name="action_permission",
            status=CheckStatus.FAILED,
            message=f"Action '{act_str}' disabled by merchant policy ({policy_flag}=False).",
            value_observed=f"{policy_flag}=False",
            threshold_applied="Policy permission must be True",
        )

    return GuardrailCheckDetail(
        name="action_permission",
        status=CheckStatus.PASSED,
        message=f"Action '{act_str}' is permitted by merchant policy ({policy_flag}=True).",
        value_observed=f"{policy_flag}=True",
        threshold_applied="Policy permission must be True",
    )


def check_transaction_limit(
    cart_value: Optional[float],
    policy: RecoveryPolicy
) -> GuardrailCheckDetail:
    """
    Check 9: Transaction Amount Limit Check.
    Requires cart_value <= policy.max_transaction_value.
    """
    if cart_value is None:
        return GuardrailCheckDetail(
            name="transaction_amount_limit",
            status=CheckStatus.FAILED,
            message="Transaction cart value is missing or unverified (fail-closed).",
            value_observed=None,
            threshold_applied=f"<= ₹{policy.max_transaction_value:,.2f}",
        )

    if cart_value > policy.max_transaction_value:
        return GuardrailCheckDetail(
            name="transaction_amount_limit",
            status=CheckStatus.FAILED,
            message=f"Transaction value (₹{cart_value:,.2f}) exceeds merchant maximum limit (₹{policy.max_transaction_value:,.2f}).",
            value_observed=round(cart_value, 2),
            threshold_applied=policy.max_transaction_value,
        )

    return GuardrailCheckDetail(
        name="transaction_amount_limit",
        status=CheckStatus.PASSED,
        message=f"Transaction value (₹{cart_value:,.2f}) is within limit (<= ₹{policy.max_transaction_value:,.2f}).",
        value_observed=round(cart_value, 2),
        threshold_applied=policy.max_transaction_value,
    )


def check_customer_contact_frequency(
    customer_id: str,
    contact_count_24h: int,
    policy: RecoveryPolicy
) -> GuardrailCheckDetail:
    """
    Check 10: Customer Contact Frequency Check.
    Requires customer interventions in rolling 24h window < policy.max_customer_contact_frequency_24h.
    """
    max_freq = policy.max_customer_contact_frequency_24h

    if contact_count_24h >= max_freq:
        return GuardrailCheckDetail(
            name="customer_contact_frequency",
            status=CheckStatus.FAILED,
            message=f"Customer contact frequency limit reached ({contact_count_24h}/{max_freq} in 24h window).",
            value_observed=contact_count_24h,
            threshold_applied=max_freq,
        )

    return GuardrailCheckDetail(
        name="customer_contact_frequency",
        status=CheckStatus.PASSED,
        message=f"Customer contact frequency ({contact_count_24h}/{max_freq} in 24h) is within limit.",
        value_observed=contact_count_24h,
        threshold_applied=max_freq,
    )


def check_manual_review_conditions(
    cart_value: float,
    intent_score: float,
    previous_purchases: int,
    session_duration: int,
    policy: RecoveryPolicy
) -> Optional[str]:
    """
    Check 11: High-Value / Behavioral Uncertainty Manual Review Filter.
    Returns a review reason string if manual human review is warranted, else None.
    """
    # Trigger 1: Very high transaction value with uncertain behavioral signals
    if cart_value >= policy.high_value_review_threshold:
        if previous_purchases == 0 or intent_score < 40.0:
            return (
                f"High-value cart (₹{cart_value:,.2f} >= ₹{policy.high_value_review_threshold:,.2f}) "
                f"with cold/uncertain customer profile (orders={previous_purchases}, intent={intent_score:.1f}) "
                f"requires manual compliance review."
            )

    # Trigger 2: Anomalous short session with disproportionately huge cart value
    if cart_value > 25000.0 and session_duration < 15 and previous_purchases == 0:
        return (
            f"Anomalous session duration ({session_duration}s) on high-value basket (₹{cart_value:,.2f}) "
            f"warrants manual verification before outreach."
        )

    return None


# ============================================================================
# Core Guardrail Engine Class
# ============================================================================

class GuardrailEngine:
    """
    RecoverAI Guardrail Engine Service.
    Applies comprehensive safety checks, idempotency, and audit logging.
    """

    def __init__(self):
        pass

    def validate(
        self,
        decision: Union[DecisionResult, RecoveryDecision, Dict[str, Any]],
        context: Optional[Union[AIDecisionContext, Dict[str, Any]]] = None,
        current_purchase_status: Optional[str] = None,
        policy_overrides: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        idempotency_key: Optional[str] = None,
        recovery_attempt_count: int = 0,
        minutes_since_last_attempt: Optional[float] = None,
        contact_count_24h: int = 0,
    ) -> GuardrailValidationResult:
        """
        Executes complete multi-point guardrail validation pipeline:
        1. Checks Idempotency cache to prevent duplicate processing
        2. Executes all 10 modular safety and policy checks without silent short-circuiting
        3. Evaluates high-value manual review conditions
        4. Assigns composite status (APPROVED, BLOCKED, REVIEW_REQUIRED) and execution state
        5. Persists tamper-evident audit record to database
        """
        # Normalize decision dict
        if isinstance(decision, DecisionResult):
            dec_dict = decision.to_dict()
        elif hasattr(decision, "to_dict"):
            dec_dict = decision.to_dict()
        elif isinstance(decision, dict):
            dec_dict = dict(decision)
        else:
            raise TypeError(f"Unsupported decision type: {type(decision)}")

        event_id = str(dec_dict.get("event_id", "evt_unknown"))
        customer_id = str(dec_dict.get("customer_id", "cust_unknown"))
        decision_id = str(dec_dict.get("decision_id", f"dec_{uuid.uuid4().hex[:12]}"))
        action_val = str(dec_dict.get("selected_action", dec_dict.get("action", "NO_ACTION")))
        
        try:
            action = RecoveryAction(action_val)
        except Exception:
            action = RecoveryAction.NO_ACTION

        # Resolve Policy
        policy = get_recovery_policy(policy_overrides)

        # 1. Idempotency Check
        computed_idempotency_key = idempotency_key or f"{event_id}:{action.value}:{policy.policy_version}"
        if db:
            existing_audit = get_audit_log_by_idempotency_key(db, computed_idempotency_key)
            if existing_audit:
                logger.info(f"Idempotency match found for key '{computed_idempotency_key}'. Returning existing audit log.")
                return self._audit_to_validation_result(existing_audit, action)

        # Normalize Context Telemetry
        ctx_dict = {}
        if isinstance(context, AIDecisionContext):
            ctx_dict = context.model_dump()
        elif hasattr(context, "to_dict"):
            ctx_dict = context.to_dict()
        elif isinstance(context, dict):
            ctx_dict = dict(context)

        # Telemetry fields (fallback from decision if not in context)
        cart_value = float(
            ctx_dict.get("cart_value")
            or dec_dict.get("cart_value")
            or dec_dict.get("revenue_at_risk")
            or 0.0
        )
        risk_score = float(
            ctx_dict.get("risk_score")
            or dec_dict.get("risk_score")
            or 0.0
        )
        recovery_prob = float(
            dec_dict.get("estimated_recovery_probability")
            or dec_dict.get("recovery_probability")
            or 0.0
        )
        expected_rec_val = float(
            dec_dict.get("expected_recovery_value")
            or (cart_value * recovery_prob)
            or 0.0
        )
        intent_score = float(ctx_dict.get("purchase_intent_score", 50.0))
        prev_purchases = int(ctx_dict.get("previous_purchases", 0))
        session_duration = int(ctx_dict.get("session_duration", 300))

        # Real-time Purchase Status (prioritize current_purchase_status param, then context, then decision)
        if current_purchase_status is not None:
            effective_purchase_status = current_purchase_status
        elif "purchase_status" in ctx_dict:
            effective_purchase_status = ctx_dict["purchase_status"]
        elif "purchase_status" in dec_dict:
            effective_purchase_status = dec_dict["purchase_status"]
        else:
            effective_purchase_status = None


        # Database telemetry enrichment if db provided
        recent_event_logs = []
        if db:
            try:
                recent_event_logs = get_recent_audit_logs_for_event(db, event_id, action=action.value)
                if contact_count_24h == 0:
                    cust_logs_24h = get_audit_logs_by_customer_id(db, customer_id, since_hours=24)
                    contact_count_24h = len(cust_logs_24h)
            except Exception as e:
                logger.warning(f"Error querying recent logs: {e}")

        # 2. Run All Modular Guardrail Checks (Don't short-circuit!)
        checks: List[GuardrailCheckDetail] = []
        blocked_reasons: List[str] = []

        # Check 1: Real-time Purchase Completion
        c1 = check_purchase_completion(effective_purchase_status)
        checks.append(c1)
        if c1.status == CheckStatus.FAILED:
            blocked_reasons.append(c1.message)

        # Check 2: Risk Score Threshold
        c2 = check_risk_threshold(risk_score, policy)
        checks.append(c2)
        if c2.status == CheckStatus.FAILED:
            blocked_reasons.append(c2.message)

        # Check 3: Recovery Probability Threshold
        c3 = check_recovery_probability(recovery_prob, policy)
        checks.append(c3)
        if c3.status == CheckStatus.FAILED:
            blocked_reasons.append(c3.message)

        # Check 4: Expected Recovery Value Threshold
        c4 = check_expected_recovery_value(expected_rec_val, policy)
        checks.append(c4)
        if c4.status == CheckStatus.FAILED:
            blocked_reasons.append(c4.message)

        # Check 5: Maximum Recovery Attempts Count
        c5 = check_max_attempts(recovery_attempt_count, policy)
        checks.append(c5)
        if c5.status == CheckStatus.FAILED:
            blocked_reasons.append(c5.message)

        # Check 6: Cooldown Window Quiet Time
        c6 = check_cooldown_window(minutes_since_last_attempt, policy)
        checks.append(c6)
        if c6.status == CheckStatus.FAILED:
            blocked_reasons.append(c6.message)

        # Check 7: Duplicate Action Prevention
        c7 = check_duplicate_action(event_id, action, recent_event_logs)
        checks.append(c7)
        if c7.status == CheckStatus.FAILED:
            blocked_reasons.append(c7.message)

        # Check 8: Merchant Action Permission Policy
        c8 = check_action_permission(action, policy)
        checks.append(c8)
        if c8.status == CheckStatus.FAILED:
            blocked_reasons.append(c8.message)

        # Check 9: Transaction Amount Limit
        c9 = check_transaction_limit(cart_value, policy)
        checks.append(c9)
        if c9.status == CheckStatus.FAILED:
            blocked_reasons.append(c9.message)

        # Check 10: Customer Contact Frequency in Rolling 24h
        c10 = check_customer_contact_frequency(customer_id, contact_count_24h, policy)
        checks.append(c10)
        if c10.status == CheckStatus.FAILED:
            blocked_reasons.append(c10.message)

        # 3. Check Manual Review Trigger (Check 11)
        manual_review_reason = check_manual_review_conditions(
            cart_value=cart_value,
            intent_score=intent_score,
            previous_purchases=prev_purchases,
            session_duration=session_duration,
            policy=policy,
        )

        checks_passed = sum(1 for c in checks if c.status == CheckStatus.PASSED)
        checks_failed = sum(1 for c in checks if c.status == CheckStatus.FAILED)

        # 4. Composite Status & Execution State Determination
        if checks_failed > 0:
            final_status = GuardrailStatus.BLOCKED
            final_exec_state = ExecutionState.BLOCKED
        elif manual_review_reason is not None:
            final_status = GuardrailStatus.REVIEW_REQUIRED
            final_exec_state = ExecutionState.REVIEW_REQUIRED
            blocked_reasons.append(manual_review_reason)
            checks.append(GuardrailCheckDetail(
                name="manual_review_filter",
                status=CheckStatus.FLAGGED,
                message=manual_review_reason,
                value_observed=cart_value,
                threshold_applied=policy.high_value_review_threshold,
            ))
        else:
            final_status = GuardrailStatus.APPROVED
            final_exec_state = ExecutionState.READY_FOR_EXECUTION

        result = GuardrailValidationResult(
            decision_id=decision_id,
            event_id=event_id,
            customer_id=customer_id,
            status=final_status,
            execution_state=final_exec_state,
            action=action,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            checks=checks,
            blocked_reasons=blocked_reasons,
            reasons=blocked_reasons if blocked_reasons else ["All policy and safety guardrail checks passed."],
            policy_version=policy.policy_version,
            idempotency_key=computed_idempotency_key,
        )

        # 5. Persist Immutable Audit Log in DB
        if db:
            try:
                log_payload = {
                    "decision_id": decision_id,
                    "event_id": event_id,
                    "customer_id": customer_id,
                    "requested_action": action.value,
                    "final_action": action.value,
                    "status": final_status.value,
                    "execution_state": final_exec_state.value,
                    "risk_score": risk_score,
                    "recovery_probability": recovery_prob,
                    "expected_recovery_value": expected_rec_val,
                    "cart_value": cart_value,
                    "policy_version": policy.policy_version,
                    "checks_passed": checks_passed,
                    "checks_failed": checks_failed,
                    "checks": [c.to_dict() for c in checks],
                    "blocked_reasons": blocked_reasons,
                    "reasons": result.reasons,
                    "reason": "; ".join(blocked_reasons) if blocked_reasons else "All guardrail checks passed.",
                    "idempotency_key": computed_idempotency_key,
                }
                save_guardrail_audit_log(db, log_payload)
            except Exception as audit_err:
                logger.warning(f"Failed to persist guardrail audit log: {audit_err}")

        return result

    def _audit_to_validation_result(
        self,
        audit: GuardrailAuditLog,
        action: RecoveryAction
    ) -> GuardrailValidationResult:
        """Convert persisted GuardrailAuditLog back to GuardrailValidationResult."""
        d = audit.to_dict()
        status_enum = GuardrailStatus(d["status"])
        state_enum = ExecutionState(d["execution_state"])
        
        parsed_checks = [
            GuardrailCheckDetail(
                name=c.get("name", "check"),
                status=CheckStatus(c.get("status", "PASSED")),
                message=c.get("message", ""),
                value_observed=c.get("value_observed"),
                threshold_applied=c.get("threshold_applied"),
            )
            for c in d.get("checks", [])
        ]

        return GuardrailValidationResult(
            decision_id=d["decision_id"],
            event_id=d["event_id"],
            customer_id=d["customer_id"],
            status=status_enum,
            execution_state=state_enum,
            action=action,
            checks_passed=d["checks_passed"],
            checks_failed=d["checks_failed"],
            checks=parsed_checks,
            blocked_reasons=d.get("blocked_reasons", []),
            reasons=d.get("reasons", []),
            policy_version=d["policy_version"],
            idempotency_key=d.get("idempotency_key"),
        )


# Global singleton instance
guardrail_engine_service = GuardrailEngine()

__all__ = [
    "check_purchase_completion",
    "check_risk_threshold",
    "check_recovery_probability",
    "check_expected_recovery_value",
    "check_max_attempts",
    "check_cooldown_window",
    "check_duplicate_action",
    "check_action_permission",
    "check_transaction_limit",
    "check_customer_contact_frequency",
    "check_manual_review_conditions",
    "GuardrailEngine",
    "guardrail_engine_service",
]
