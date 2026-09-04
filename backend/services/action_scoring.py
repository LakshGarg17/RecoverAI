"""
RecoverAI Action Scoring Engine (Day 5)

Calculates deterministic scores for candidate recovery actions.

Core principle:
    Action Score =
        Expected Recovery Value
        - Customer Friction
        - Action Cost
        - Risk Penalty
        + AI Alignment Bonus

The scoring is deterministic and explainable.

Important:
- AI does NOT directly execute actions.
- AI recommendation is only one scoring input.
- Merchant policy remains the final eligibility gate.
- High-intent customers can legitimately favor PAYMENT_LINK
  when the expected recovery benefit justifies the additional friction.
"""

from __future__ import annotations

import math
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field

from ai.schemas import (
    RecoveryAction,
    AIDecisionContext,
    AIDiagnosisResult,
)

from backend.config.recovery_policy import (
    RecoveryPolicy,
    DEFAULT_RECOVERY_POLICY,
)


# ============================================================================
# Estimated Action Recovery Probabilities
# ============================================================================
#
# These are heuristic starting calibration assumptions.
# They should be recalibrated later using measured recovery outcomes.
# ============================================================================

ESTIMATED_ACTION_RECOVERY_PROB_NO_ACTION: float = 0.05
ESTIMATED_ACTION_RECOVERY_PROB_DELAYED_FOLLOW_UP: float = 0.45
ESTIMATED_ACTION_RECOVERY_PROB_CHECKOUT_REMINDER: float = 0.65
ESTIMATED_ACTION_RECOVERY_PROB_PERSONALIZED_REMINDER: float = 0.78

# Payment links have the highest assumed conversion because they
# remove checkout friction for customers who already demonstrate
# strong purchase intent.
ESTIMATED_ACTION_RECOVERY_PROB_PAYMENT_LINK: float = 0.84


ACTION_BASE_PROBABILITIES: Dict[RecoveryAction, float] = {
    RecoveryAction.NO_ACTION:
        ESTIMATED_ACTION_RECOVERY_PROB_NO_ACTION,

    RecoveryAction.DELAYED_FOLLOW_UP:
        ESTIMATED_ACTION_RECOVERY_PROB_DELAYED_FOLLOW_UP,

    RecoveryAction.CHECKOUT_REMINDER:
        ESTIMATED_ACTION_RECOVERY_PROB_CHECKOUT_REMINDER,

    RecoveryAction.PERSONALIZED_REMINDER:
        ESTIMATED_ACTION_RECOVERY_PROB_PERSONALIZED_REMINDER,

    RecoveryAction.PAYMENT_LINK:
        ESTIMATED_ACTION_RECOVERY_PROB_PAYMENT_LINK,
}


# ============================================================================
# Customer Friction / Cost
# ============================================================================

ACTION_FRICTION_METRICS: Dict[RecoveryAction, Dict[str, Any]] = {

    RecoveryAction.NO_ACTION: {
        "level": "LOW",
        "base_friction": 0.0,
        "base_cost": 0.0,
    },

    RecoveryAction.DELAYED_FOLLOW_UP: {
        "level": "LOW",
        "base_friction": 5.0,
        "base_cost": 2.0,
    },

    RecoveryAction.CHECKOUT_REMINDER: {
        "level": "LOW",
        "base_friction": 8.0,
        "base_cost": 4.0,
    },

    RecoveryAction.PERSONALIZED_REMINDER: {
        "level": "MEDIUM",
        "base_friction": 12.0,
        "base_cost": 6.0,
    },

    RecoveryAction.PAYMENT_LINK: {
        "level": "HIGH",
        "base_friction": 18.0,
        "base_cost": 8.0,
    },
}


# ============================================================================
# Scored Action Model
# ============================================================================

class ScoredAction(BaseModel):
    """
    Detailed scoring breakdown for an evaluated recovery action.
    """

    action: RecoveryAction

    score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Normalized action score (0-100)",
    )

    expected_recovery_value: float = Field(
        ...,
        description=(
            "Revenue at risk multiplied by effective "
            "action recovery probability"
        ),
    )

    estimated_recovery_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Effective recovery probability",
    )

    friction_level: str = Field(
        ...,
        description="Customer friction level",
    )

    friction_deduction: float = Field(default=0.0)

    action_cost: float = Field(default=0.0)

    risk_penalty: float = Field(default=0.0)

    value_score: float = Field(default=0.0)

    is_eligible: bool = Field(default=True)

    rejection_reason: Optional[str] = Field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": (
                self.action.value
                if hasattr(self.action, "value")
                else str(self.action)
            ),
            "score": round(self.score, 1),
            "expected_recovery_value": round(
                self.expected_recovery_value,
                2,
            ),
            "estimated_recovery_probability": round(
                self.estimated_recovery_probability,
                2,
            ),
            "friction_level": self.friction_level,
            "friction_deduction": round(
                self.friction_deduction,
                1,
            ),
            "action_cost": round(
                self.action_cost,
                1,
            ),
            "risk_penalty": round(
                self.risk_penalty,
                1,
            ),
            "value_score": round(
                self.value_score,
                1,
            ),
            "is_eligible": self.is_eligible,
            "rejection_reason": self.rejection_reason,
        }


# ============================================================================
# Effective Recovery Probability
# ============================================================================

def compute_effective_action_probability(
    action: RecoveryAction,
    context: AIDecisionContext,
    ai_diagnosis: Optional[AIDiagnosisResult] = None,
) -> float:
    """
    Compute calibrated action-specific recovery probability.

    Inputs:
    - Base action probability
    - Purchase intent
    - Customer history
    - AI diagnosis probability
    - Action-specific high-intent behavior

    The output is bounded between 5% and 98%.
    """

    base_prob = ACTION_BASE_PROBABILITIES.get(
        action,
        0.10,
    )

    # NO_ACTION uses a fixed probability.
    if action == RecoveryAction.NO_ACTION:
        return ESTIMATED_ACTION_RECOVERY_PROB_NO_ACTION

    # ------------------------------------------------------------------
    # General purchase-intent factor
    # ------------------------------------------------------------------

    intent_factor = max(
        0.2,
        min(
            1.3,
            0.5
            + (context.purchase_intent_score / 100.0) * 0.7,
        ),
    )

    # ------------------------------------------------------------------
    # Payment Link gets stronger benefit from very high purchase intent.
    #
    # Rationale:
    # A customer who has already demonstrated strong purchase intent
    # is more likely to benefit from a direct payment path.
    # ------------------------------------------------------------------

    if action == RecoveryAction.PAYMENT_LINK:

        if context.purchase_intent_score >= 85.0:
            intent_factor = max(
                intent_factor,
                min(
                    1.45,
                    0.35
                    + (context.purchase_intent_score / 100.0) * 1.10,
                ),
            )

        elif context.purchase_intent_score >= 70.0:
            intent_factor = max(
                intent_factor,
                min(
                    1.25,
                    0.40
                    + (context.purchase_intent_score / 100.0) * 0.90,
                ),
            )

    # ------------------------------------------------------------------
    # Customer history factor
    # ------------------------------------------------------------------

    history_factor = 1.0

    if context.previous_purchases >= 1:

        # Repeat customers respond especially well to
        # relationship-based reminders.
        if action in (
            RecoveryAction.PERSONALIZED_REMINDER,
            RecoveryAction.CHECKOUT_REMINDER,
        ):
            history_factor = 1.10

    else:

        # First-time customers receive a modest reduction for
        # high-pressure payment links.
        if action == RecoveryAction.PAYMENT_LINK:

            # For extremely strong purchase intent, the evidence
            # partially offsets the first-time-customer penalty.
            if context.purchase_intent_score >= 85.0:
                history_factor = 0.97
            else:
                history_factor = 0.92

    # ------------------------------------------------------------------
    # AI diagnosis blend
    # ------------------------------------------------------------------

    ai_blend_factor = 1.0

    if ai_diagnosis:

        # AI recommendation alignment receives a small boost.
        if ai_diagnosis.recommended_action == action:
            ai_blend_factor = 1.05

        ai_prob = ai_diagnosis.recovery_probability

        calibrated = (
            (
                base_prob
                * intent_factor
                * history_factor
                * 0.75
            )
            +
            (
                ai_prob
                * 0.25
                * ai_blend_factor
            )
        )

    else:

        calibrated = (
            base_prob
            * intent_factor
            * history_factor
        )

    return round(
        float(
            min(
                0.98,
                max(
                    0.05,
                    calibrated,
                ),
            )
        ),
        2,
    )


# ============================================================================
# Score One Action
# ============================================================================

def score_single_action(
    action: RecoveryAction,
    context: AIDecisionContext,
    ai_diagnosis: Optional[AIDiagnosisResult] = None,
    policy: Optional[RecoveryPolicy] = None,
) -> ScoredAction:
    """
    Calculate:

        Action Score =
            Value Score
            - Customer Friction
            - Action Cost
            - Risk Penalty
            + AI Alignment Bonus

    Result is clamped to [0, 100].
    """

    metrics = ACTION_FRICTION_METRICS.get(
        action,
        {
            "level": "MEDIUM",
            "base_friction": 15.0,
            "base_cost": 5.0,
        },
    )

    friction_level = metrics["level"]

    friction_deduction = float(
        metrics["base_friction"]
    )

    action_cost = float(
        metrics["base_cost"]
    )

    risk_penalty = 0.0

    # ------------------------------------------------------------------
    # Effective probability + expected value
    # ------------------------------------------------------------------

    effective_prob = compute_effective_action_probability(
        action=action,
        context=context,
        ai_diagnosis=ai_diagnosis,
    )

    revenue_at_risk = float(
        context.revenue_at_risk
        or context.cart_value
        or 0.0
    )

    expected_recovery_val = round(
        revenue_at_risk * effective_prob,
        2,
    )

    # ------------------------------------------------------------------
    # NO ACTION
    # ------------------------------------------------------------------

    if action == RecoveryAction.NO_ACTION:

        if (
            revenue_at_risk <= 100.0
            or context.purchase_intent_score < 30.0
            or context.risk_score < 30.0
        ):

            final_score = (
                85.0
                - (
                    context.purchase_intent_score
                    * 0.5
                )
            )

        else:

            final_score = max(
                5.0,
                45.0
                - (
                    context.purchase_intent_score
                    * 0.4
                )
                - min(
                    25.0,
                    expected_recovery_val / 200.0,
                ),
            )

        final_score = max(
            0.0,
            min(
                100.0,
                final_score,
            ),
        )

        return ScoredAction(
            action=action,
            score=round(
                final_score,
                1,
            ),
            expected_recovery_value=expected_recovery_val,
            estimated_recovery_probability=effective_prob,
            friction_level="LOW",
            friction_deduction=0.0,
            action_cost=0.0,
            risk_penalty=0.0,
            value_score=0.0,
            is_eligible=True,
        )

    # ------------------------------------------------------------------
    # Value score
    # ------------------------------------------------------------------

    val_magnitude_score = min(
        25.0,
        math.log10(
            max(
                10.0,
                revenue_at_risk,
            )
        ) * 6.5,
    )

    prob_score = effective_prob * 50.0

    intent_score_component = (
        context.purchase_intent_score
        / 100.0
    ) * 20.0

    value_score = (
        prob_score
        + val_magnitude_score
        + intent_score_component
    )

    # ------------------------------------------------------------------
    # Contextual friction adjustments
    # ------------------------------------------------------------------

    if action == RecoveryAction.PERSONALIZED_REMINDER:

        if (
            context.previous_purchases >= 1
            or context.customer_lifetime_value > 3000.0
        ):
            # Existing customer relationship makes personalization
            # less intrusive.
            friction_deduction = max(
                3.0,
                friction_deduction - 5.0,
            )

        elif context.previous_purchases == 0:

            # Cold customer + personalization can feel less natural.
            friction_deduction += 4.0
            risk_penalty += 3.0

    # ------------------------------------------------------------------
    # PAYMENT LINK
    # ------------------------------------------------------------------

    elif action == RecoveryAction.PAYMENT_LINK:

        # Payment Links are intentionally high-friction by default.
        #
        # However, when the customer has already demonstrated very
        # strong purchase intent, the direct payment path becomes
        # substantially more appropriate.
        if context.purchase_intent_score >= 85.0:

            # Strong intent means the customer is already close to
            # completing the purchase.
            friction_deduction = max(
                10.0,
                friction_deduction - 8.0,
            )

            # High intent reduces uncertainty for a direct payment
            # request.
            risk_penalty += 0.0

        elif context.purchase_intent_score >= 70.0:

            friction_deduction = max(
                14.0,
                friction_deduction - 4.0,
            )

        else:

            # Low intent makes an instant payment request aggressive.
            risk_penalty += 10.0

        # First-time customer penalty remains, but is smaller for
        # extremely high-intent customers.
        if context.previous_purchases == 0:

            if context.purchase_intent_score >= 85.0:
                risk_penalty += 3.0
            else:
                risk_penalty += 8.0

        # Small carts don't justify a high-friction direct payment path.
        if revenue_at_risk < 500.0:
            risk_penalty += 6.0

    # ------------------------------------------------------------------
    # CHECKOUT REMINDER
    # ------------------------------------------------------------------

    elif action == RecoveryAction.CHECKOUT_REMINDER:

        if context.purchase_intent_score >= 50.0:
            friction_deduction = max(
                4.0,
                friction_deduction - 4.0,
            )

    # ------------------------------------------------------------------
    # DELAYED FOLLOW-UP
    # ------------------------------------------------------------------

    elif action == RecoveryAction.DELAYED_FOLLOW_UP:

        if (
            35.0
            <= context.purchase_intent_score
            <= 65.0
        ):

            value_score += 8.0

        elif context.purchase_intent_score > 80.0:

            # Delaying a highly interested customer can lose momentum.
            risk_penalty += 10.0

    # ------------------------------------------------------------------
    # AI Recommendation Alignment
    # ------------------------------------------------------------------

    ai_alignment_bonus = 0.0

    if (
        ai_diagnosis
        and ai_diagnosis.recommended_action == action
    ):

        ai_alignment_bonus = (
            4.0
            * ai_diagnosis.recommendation_confidence
        )

    # ------------------------------------------------------------------
    # Final score
    # ------------------------------------------------------------------

    raw_score = (
        value_score
        - friction_deduction
        - action_cost
        - risk_penalty
        + ai_alignment_bonus
    )

    final_score = round(
        max(
            0.0,
            min(
                100.0,
                raw_score,
            ),
        ),
        1,
    )

    return ScoredAction(
        action=action,
        score=final_score,
        expected_recovery_value=expected_recovery_val,
        estimated_recovery_probability=effective_prob,
        friction_level=friction_level,
        friction_deduction=friction_deduction,
        action_cost=action_cost,
        risk_penalty=risk_penalty,
        value_score=value_score,
        is_eligible=True,
    )


# ============================================================================
# Score All Candidate Actions
# ============================================================================

def score_all_candidate_actions(
    context: AIDecisionContext,
    eligible_actions: List[RecoveryAction],
    ai_diagnosis: Optional[AIDiagnosisResult] = None,
    policy: Optional[RecoveryPolicy] = None,
) -> List[ScoredAction]:
    """
    Score all eligible candidate actions.

    Results are sorted by descending decision score.
    """

    scored_list: List[ScoredAction] = []

    for action in eligible_actions:

        scored = score_single_action(
            action=action,
            context=context,
            ai_diagnosis=ai_diagnosis,
            policy=policy,
        )

        scored_list.append(scored)

    # Highest score first.
    scored_list.sort(
        key=lambda x: x.score,
        reverse=True,
    )

    return scored_list


# ============================================================================
# Public Exports
# ============================================================================

__all__ = [
    "ESTIMATED_ACTION_RECOVERY_PROB_NO_ACTION",
    "ESTIMATED_ACTION_RECOVERY_PROB_DELAYED_FOLLOW_UP",
    "ESTIMATED_ACTION_RECOVERY_PROB_CHECKOUT_REMINDER",
    "ESTIMATED_ACTION_RECOVERY_PROB_PERSONALIZED_REMINDER",
    "ESTIMATED_ACTION_RECOVERY_PROB_PAYMENT_LINK",
    "ACTION_BASE_PROBABILITIES",
    "ACTION_FRICTION_METRICS",
    "ScoredAction",
    "compute_effective_action_probability",
    "score_single_action",
    "score_all_candidate_actions",
]