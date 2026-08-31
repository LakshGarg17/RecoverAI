"""
RecoverAI Autonomous Recovery Decision Engine (Day 5)
Orchestrates deterministic recovery action selection on top of AI diagnosis.
Pipeline: Event -> Risk Engine -> AI Diagnosis -> Candidate Actions -> Eligibility Filter
          -> Action Scoring -> Policy Thresholds -> Best Action Selection -> Persistence.
"""

import os
import sys
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
from pydantic import BaseModel, Field
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
    PriorityTier,
    AIDiagnosisResult,
    AIDecisionContext,
    DiagnoseEventResponse,
)
from ai.diagnosis import (
    build_ai_decision_context,
    ai_diagnosis_agent,
    get_processed_dataset,
)
from backend.config.recovery_policy import RecoveryPolicy, DEFAULT_RECOVERY_POLICY, get_recovery_policy
from backend.services.action_scoring import (
    ScoredAction,
    score_all_candidate_actions,
    score_single_action,
)
from database.decision_models import RecoveryDecision, save_recovery_decision

logger = logging.getLogger(__name__)

# Full candidate action universe
ALL_CANDIDATE_ACTIONS: List[RecoveryAction] = [
    RecoveryAction.CHECKOUT_REMINDER,
    RecoveryAction.PERSONALIZED_REMINDER,
    RecoveryAction.PAYMENT_LINK,
    RecoveryAction.DELAYED_FOLLOW_UP,
    RecoveryAction.NO_ACTION,
]


class ExcludedActionDetail(BaseModel):
    """Details of candidate actions disqualified by eligibility filters or merchant policy."""
    action: str
    reason: str


class AlternativeActionDetail(BaseModel):
    """Summary of scored alternative actions."""
    action: str
    score: float
    expected_recovery_value: float
    estimated_recovery_probability: float
    friction_level: str


class DecisionResult(BaseModel):
    """
    Structured outcome of the RecoverAI Decision Engine.
    """
    decision_id: str
    event_id: str
    customer_id: str
    risk_score: float
    priority: str
    selected_action: RecoveryAction
    decision_score: float
    expected_recovery_value: float
    estimated_recovery_probability: float
    explanation: str
    reasons: List[str]
    alternative_actions: List[AlternativeActionDetail]
    excluded_actions: List[ExcludedActionDetail]
    ai_recommendation: Optional[Dict[str, Any]] = None
    divergence_reason: Optional[str] = None
    policy_applied: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "event_id": self.event_id,
            "customer_id": self.customer_id,
            "risk_score": round(self.risk_score, 1),
            "priority": self.priority,
            "selected_action": self.selected_action.value if hasattr(self.selected_action, "value") else str(self.selected_action),
            "decision_score": round(self.decision_score, 1),
            "expected_recovery_value": round(self.expected_recovery_value, 2),
            "estimated_recovery_probability": round(self.estimated_recovery_probability, 2),
            "explanation": self.explanation,
            "reasons": self.reasons,
            "alternative_actions": [a.model_dump() for a in self.alternative_actions],
            "excluded_actions": [e.model_dump() for e in self.excluded_actions],
            "ai_recommendation": self.ai_recommendation,
            "divergence_reason": self.divergence_reason,
            "policy_applied": self.policy_applied,
        }


def filter_eligible_actions(
    context: AIDecisionContext,
    policy: RecoveryPolicy
) -> Tuple[List[RecoveryAction], List[ExcludedActionDetail]]:
    """
    Evaluates candidate action eligibility based on event state, customer telemetry,
    and merchant recovery policy rules.
    Returns:
      (eligible_actions, excluded_actions_with_reasons)
    """
    eligible: List[RecoveryAction] = []
    excluded: List[ExcludedActionDetail] = []

    # 1. NO_ACTION is unconditionally eligible
    eligible.append(RecoveryAction.NO_ACTION)

    # If event is already completed/successful or cart is 0, exclude all outreach
    if context.purchase_status not in ("abandoned", "pending", "failed"):
        for act in [RecoveryAction.CHECKOUT_REMINDER, RecoveryAction.PERSONALIZED_REMINDER,
                    RecoveryAction.PAYMENT_LINK, RecoveryAction.DELAYED_FOLLOW_UP]:
            excluded.append(ExcludedActionDetail(
                action=act.value,
                reason=f"Purchase status is '{context.purchase_status}' (not abandoned)."
            ))
        return eligible, excluded

    if context.cart_value <= 0.0:
        for act in [RecoveryAction.CHECKOUT_REMINDER, RecoveryAction.PERSONALIZED_REMINDER,
                    RecoveryAction.PAYMENT_LINK, RecoveryAction.DELAYED_FOLLOW_UP]:
            excluded.append(ExcludedActionDetail(
                action=act.value,
                reason="Cart value is zero or unrecorded."
            ))
        return eligible, excluded

    # 2. CHECKOUT_REMINDER
    # Eligible for abandoned carts with active value
    eligible.append(RecoveryAction.CHECKOUT_REMINDER)

    # 3. PERSONALIZED_REMINDER
    if not policy.allow_personalized_messages:
        excluded.append(ExcludedActionDetail(
            action=RecoveryAction.PERSONALIZED_REMINDER.value,
            reason="Disabled by merchant recovery policy (allow_personalized_messages=False)."
        ))
    else:
        eligible.append(RecoveryAction.PERSONALIZED_REMINDER)

    # 4. PAYMENT_LINK
    # Requires policy permission, minimum cart value, and minimum purchase intent
    if not policy.allow_payment_links:
        excluded.append(ExcludedActionDetail(
            action=RecoveryAction.PAYMENT_LINK.value,
            reason="Disabled by merchant recovery policy (allow_payment_links=False)."
        ))
    elif context.cart_value < policy.min_cart_value_for_payment_link:
        excluded.append(ExcludedActionDetail(
            action=RecoveryAction.PAYMENT_LINK.value,
            reason=(
                f"Cart value (₹{context.cart_value:,.2f}) below minimum policy threshold "
                f"(₹{policy.min_cart_value_for_payment_link:,.2f}) for direct payment link dispatch."
            )
        ))
    elif context.purchase_intent_score < policy.min_intent_for_payment_link:
        excluded.append(ExcludedActionDetail(
            action=RecoveryAction.PAYMENT_LINK.value,
            reason=(
                f"Purchase intent score ({context.purchase_intent_score:.1f}/100) below minimum required "
                f"intent ({policy.min_intent_for_payment_link:.1f}) for high-friction payment links."
            )
        ))
    else:
        eligible.append(RecoveryAction.PAYMENT_LINK)

    # 5. DELAYED_FOLLOW_UP
    # Always eligible for abandoned carts
    eligible.append(RecoveryAction.DELAYED_FOLLOW_UP)

    return eligible, excluded


def generate_decision_reasons(
    selected_action: RecoveryAction,
    selected_score: ScoredAction,
    context: AIDecisionContext,
    policy: RecoveryPolicy,
    ai_diagnosis: Optional[AIDiagnosisResult] = None
) -> List[str]:
    """
    Generates dynamic, evidence-based reason bullets derived from real scoring factors
    (cart value, purchase intent, customer history, friction comparison, policy thresholds).
    """
    reasons: List[str] = []

    # Cart Value / Revenue factor
    if context.cart_value >= 5000.0:
        reasons.append(f"High-value cart (₹{context.cart_value:,.2f} revenue at risk)")
    elif context.cart_value >= 1000.0:
        reasons.append(f"Substantial cart value (₹{context.cart_value:,.2f} at risk)")
    else:
        reasons.append(f"Modest cart value (₹{context.cart_value:,.2f})")

    # Purchase Intent & Engagement factor
    if context.purchase_intent_score >= 70.0:
        reasons.append(f"High purchase intent ({context.purchase_intent_score:.1f}/100 across {context.pages_viewed} pages)")
    elif context.purchase_intent_score >= 40.0:
        reasons.append(f"Moderate purchase intent ({context.purchase_intent_score:.1f}/100)")
    else:
        reasons.append(f"Low purchase intent ({context.purchase_intent_score:.1f}/100, session {round(context.session_duration/60, 1)}m)")

    # Customer History & CLV factor
    if context.previous_purchases >= 1:
        reasons.append(f"Repeat buyer with {context.previous_purchases} prior order(s) (₹{context.customer_lifetime_value:,.2f} CLV)")
    else:
        reasons.append("First-time prospective buyer (no prior purchase history)")

    # Action-Specific Rationale
    if selected_action == RecoveryAction.NO_ACTION:
        if selected_score.expected_recovery_value < policy.minimum_expected_value:
            reasons.append(
                f"Expected recovery value (₹{selected_score.expected_recovery_value:,.2f}) "
                f"is below merchant minimum threshold (₹{policy.minimum_expected_value:,.2f})"
            )
        else:
            reasons.append("Low recovery probability indicates autonomous outreach is not cost-effective")

    elif selected_action == RecoveryAction.PERSONALIZED_REMINDER:
        reasons.append("High recovery probability (78%) balanced with moderate customer friction")
        if context.previous_purchases >= 1:
            reasons.append("Personalized messaging maximizes engagement for existing customer relationship")

    elif selected_action == RecoveryAction.CHECKOUT_REMINDER:
        reasons.append("Least-intrusive standard reminder maximizes recovery without customer friction")

    elif selected_action == RecoveryAction.PAYMENT_LINK:
        reasons.append("Direct payment link removes checkout hurdles for high-intent immediate conversion")

    elif selected_action == RecoveryAction.DELAYED_FOLLOW_UP:
        reasons.append("Delayed cadence allows exploratory buyer consideration time before re-engagement")

    return reasons


def evaluate_ai_divergence(
    ai_diagnosis: Optional[AIDiagnosisResult],
    selected_action: RecoveryAction,
    selected_score: ScoredAction,
    policy: RecoveryPolicy,
    excluded_actions: List[ExcludedActionDetail]
) -> Optional[str]:
    """
    Detects if and why the deterministic Decision Engine deviated from the LLM's raw suggestion.
    """
    if not ai_diagnosis:
        return None

    ai_action = ai_diagnosis.recommended_action
    if ai_action == selected_action:
        return None

    # Check if AI action was excluded by policy/eligibility
    for exc in excluded_actions:
        if exc.action == ai_action.value:
            return (
                f"AI suggested {ai_action.value}; decision engine chose {selected_action.value} — "
                f"{ai_action.value} was disqualified by merchant policy: {exc.reason}"
            )

    # Check if AI action failed minimum expected value or probability threshold
    if selected_action == RecoveryAction.NO_ACTION and ai_action != RecoveryAction.NO_ACTION:
        return (
            f"AI suggested {ai_action.value}; decision engine chose NO_ACTION — "
            f"expected recovery value was below merchant policy minimum of ₹{policy.minimum_expected_value:,.2f} "
            f"or minimum probability of {policy.minimum_recovery_probability*100:.0f}%."
        )

    # Multi-attribute friction / cost trade-off divergence
    return (
        f"AI suggested {ai_action.value}; decision engine chose {selected_action.value} — "
        f"{selected_action.value} achieved a superior composite score ({selected_score.score:.1f}) by balancing "
        f"recovery value against lower customer friction and lower risk penalty."
    )


class RecoveryDecisionEngine:
    """
    Recovery Decision Engine Service.
    Applies deterministic multi-factor scoring and policy constraints to select the optimal recovery action.
    """

    def __init__(self):
        pass

    async def decide_recovery_action(
        self,
        event_data: Union[Dict[str, Any], pd.Series, str],
        policy_overrides: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        force_ai_fallback: bool = False
    ) -> DecisionResult:
        """
        Executes the end-to-end Decision Engine workflow:
        1. Builds full context (Event Telemetry + Customer Aggregates + Risk Engine)
        2. Calls Day 4 AI diagnosis agent for structured reasoning
        3. Generates candidate actions
        4. Filters eligible actions via merchant recovery policy
        5. Scores candidate actions (Value - Friction - Cost - Penalty)
        6. Enforces policy thresholds (Min Expected Value, Min Recovery Probability)
        7. Selects best action and compiles explanations
        8. Persists decision record in database
        """
        # 1. Resolve Policy
        policy = get_recovery_policy(policy_overrides)

        # 2. Build Context
        context = build_ai_decision_context(event_data)

        # 3. AI Diagnosis (Treated as 1 input, not final answer)
        try:
            ai_diagnosis_response = await ai_diagnosis_agent.diagnose_event(
                event_data=event_data,
                force_fallback=force_ai_fallback,
            )
            # Reconstruct AIDiagnosisResult from response
            ai_diagnosis = AIDiagnosisResult(
                diagnosis=ai_diagnosis_response.diagnosis,
                recovery_probability=ai_diagnosis_response.recovery_probability,
                recommended_action=ai_diagnosis_response.recommended_action,
                priority=ai_diagnosis_response.priority,
                recommendation_confidence=ai_diagnosis_response.recommendation_confidence,
                reason_codes=ai_diagnosis_response.reason_codes,
                explanation=ai_diagnosis_response.explanation,
                suggested_message=ai_diagnosis_response.suggested_message,
            )
        except Exception as e:
            logger.warning(f"AI diagnosis encountered error: {e}. Generating fallback context.")
            ai_diagnosis = None

        # 4. Filter Action Eligibility
        eligible_actions, excluded_actions = filter_eligible_actions(context, policy)

        # 5. Score Candidate Actions
        scored_actions = score_all_candidate_actions(
            context=context,
            eligible_actions=eligible_actions,
            ai_diagnosis=ai_diagnosis,
            policy=policy,
        )

        # 6. Apply Policy Thresholds & Select Best Action
        # Threshold: Disqualify active actions that do not meet min expected value or min recovery prob
        selected_scored: Optional[ScoredAction] = None

        for scored in scored_actions:
            if scored.action == RecoveryAction.NO_ACTION:
                continue

            # Check Minimum Expected Value
            if scored.expected_recovery_value < policy.minimum_expected_value:
                excluded_actions.append(ExcludedActionDetail(
                    action=scored.action.value,
                    reason=(
                        f"Expected recovery value (₹{scored.expected_recovery_value:,.2f}) is below "
                        f"merchant threshold of ₹{policy.minimum_expected_value:,.2f}."
                    )
                ))
                continue

            # Check Minimum Recovery Probability
            if scored.estimated_recovery_probability < policy.minimum_recovery_probability:
                excluded_actions.append(ExcludedActionDetail(
                    action=scored.action.value,
                    reason=(
                        f"Estimated recovery probability ({scored.estimated_recovery_probability*100:.1f}%) is below "
                        f"merchant minimum threshold of {policy.minimum_recovery_probability*100:.1f}%."
                    )
                ))
                continue

            # Highest score that passed thresholds
            selected_scored = scored
            break

        # Fallback to NO_ACTION if no active action qualifies or if NO_ACTION scored higher
        no_action_scored = next((s for s in scored_actions if s.action == RecoveryAction.NO_ACTION), None)
        if not no_action_scored:
            no_action_scored = score_single_action(RecoveryAction.NO_ACTION, context, ai_diagnosis, policy)

        if selected_scored is None:
            selected_scored = no_action_scored
        else:
            # If NO_ACTION genuinely scores higher than the best active action (e.g. ultra low intent)
            if no_action_scored.score > selected_scored.score:
                selected_scored = no_action_scored

        # 7. Format Alternatives & Reasons
        alternatives: List[AlternativeActionDetail] = [
            AlternativeActionDetail(
                action=s.action.value,
                score=s.score,
                expected_recovery_value=s.expected_recovery_value,
                estimated_recovery_probability=s.estimated_recovery_probability,
                friction_level=s.friction_level,
            )
            for s in scored_actions
            if s.action != selected_scored.action
        ]

        reasons = generate_decision_reasons(
            selected_action=selected_scored.action,
            selected_score=selected_scored,
            context=context,
            policy=policy,
            ai_diagnosis=ai_diagnosis,
        )

        divergence = evaluate_ai_divergence(
            ai_diagnosis=ai_diagnosis,
            selected_action=selected_scored.action,
            selected_score=selected_scored,
            policy=policy,
            excluded_actions=excluded_actions,
        )

        # Build Explanation sentence
        explanation = (
            f"RecoverAI Decision Engine selected {selected_scored.action.value} (Decision Score: {selected_scored.score:.1f}/100) "
            f"with estimated recovery probability of {selected_scored.estimated_recovery_probability*100:.1f}% "
            f"and expected recovery value of ₹{selected_scored.expected_recovery_value:,.2f}."
        )
        if divergence:
            explanation += f" Note: {divergence}"

        decision_id = f"dec_{uuid.uuid4().hex[:12]}"
        ai_rec_dict = {
            "action": ai_diagnosis.recommended_action.value if ai_diagnosis else None,
            "recovery_probability": ai_diagnosis.recovery_probability if ai_diagnosis else None,
            "diagnosis": ai_diagnosis.diagnosis.value if ai_diagnosis else None,
        } if ai_diagnosis else None

        result = DecisionResult(
            decision_id=decision_id,
            event_id=context.event_id,
            customer_id=context.customer_id,
            risk_score=context.risk_score,
            priority=context.priority,
            selected_action=selected_scored.action,
            decision_score=selected_scored.score,
            expected_recovery_value=selected_scored.expected_recovery_value,
            estimated_recovery_probability=selected_scored.estimated_recovery_probability,
            explanation=explanation,
            reasons=reasons,
            alternative_actions=alternatives,
            excluded_actions=excluded_actions,
            ai_recommendation=ai_rec_dict,
            divergence_reason=divergence,
            policy_applied=policy.to_dict(),
        )

        # 8. Persist Decision Record in DB if session provided
        if db:
            try:
                save_recovery_decision(db, result.to_dict())
            except Exception as db_err:
                logger.warning(f"Could not persist recovery decision to DB: {db_err}")

        return result


# Global singleton instance
decision_engine_service = RecoveryDecisionEngine()

__all__ = [
    "ALL_CANDIDATE_ACTIONS",
    "ExcludedActionDetail",
    "AlternativeActionDetail",
    "DecisionResult",
    "filter_eligible_actions",
    "generate_decision_reasons",
    "evaluate_ai_divergence",
    "RecoveryDecisionEngine",
    "decision_engine_service",
]
