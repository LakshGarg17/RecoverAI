"""
RecoverAI Backend Services Root
"""
from backend.services.risk_engine import evaluate_event_risk, batch_evaluate_events
from backend.services.action_scoring import (
    ScoredAction,
    score_single_action,
    score_all_candidate_actions,
    compute_effective_action_probability,
)
from backend.services.decision_engine import (
    RecoveryDecisionEngine,
    decision_engine_service,
    DecisionResult,
    filter_eligible_actions,
)
from backend.services.guardrail_engine import (
    GuardrailEngine,
    guardrail_engine_service,
    check_purchase_completion,
    check_risk_threshold,
    check_recovery_probability,
    check_expected_recovery_value,
    check_max_attempts,
    check_cooldown_window,
    check_duplicate_action,
    check_action_permission,
    check_transaction_limit,
    check_customer_contact_frequency,
    check_manual_review_conditions,
)

__all__ = [
    "evaluate_event_risk",
    "batch_evaluate_events",
    "ScoredAction",
    "score_single_action",
    "score_all_candidate_actions",
    "compute_effective_action_probability",
    "RecoveryDecisionEngine",
    "decision_engine_service",
    "DecisionResult",
    "filter_eligible_actions",
    "GuardrailEngine",
    "guardrail_engine_service",
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
]


