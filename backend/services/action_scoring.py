"""
RecoverAI Action Scoring Engine (Day 5)
Calculates deterministic scores for candidate recovery actions.
Action Score = Expected Recovery Value − Customer Friction − Action Cost − Risk Penalty (0-100).
"""

import math
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ai.schemas import RecoveryAction, AIDecisionContext, AIDiagnosisResult
from backend.config.recovery_policy import RecoveryPolicy, DEFAULT_RECOVERY_POLICY


# ============================================================================
# Named Starting Assumptions: Estimated Action Recovery Probabilities
# Note: These are heuristic starting calibration assumptions, not final statistics.
# Easy to recalibrate in future iterations (e.g. Day 9).
# ============================================================================
ESTIMATED_ACTION_RECOVERY_PROB_NO_ACTION: float = 0.05
ESTIMATED_ACTION_RECOVERY_PROB_DELAYED_FOLLOW_UP: float = 0.45
ESTIMATED_ACTION_RECOVERY_PROB_CHECKOUT_REMINDER: float = 0.65
ESTIMATED_ACTION_RECOVERY_PROB_PERSONALIZED_REMINDER: float = 0.78
ESTIMATED_ACTION_RECOVERY_PROB_PAYMENT_LINK: float = 0.84

ACTION_BASE_PROBABILITIES: Dict[RecoveryAction, float] = {
    RecoveryAction.NO_ACTION: ESTIMATED_ACTION_RECOVERY_PROB_NO_ACTION,
    RecoveryAction.DELAYED_FOLLOW_UP: ESTIMATED_ACTION_RECOVERY_PROB_DELAYED_FOLLOW_UP,
    RecoveryAction.CHECKOUT_REMINDER: ESTIMATED_ACTION_RECOVERY_PROB_CHECKOUT_REMINDER,
    RecoveryAction.PERSONALIZED_REMINDER: ESTIMATED_ACTION_RECOVERY_PROB_PERSONALIZED_REMINDER,
    RecoveryAction.PAYMENT_LINK: ESTIMATED_ACTION_RECOVERY_PROB_PAYMENT_LINK,
}

# Customer Friction Ratings & Deductions (0 - 100 point scale impact)
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



class ScoredAction(BaseModel):
    """
    Detailed scoring breakdown for an evaluated candidate action.
    """
    action: RecoveryAction
    score: float = Field(..., ge=0.0, le=100.0, description="Normalized action score (0-100)")
    expected_recovery_value: float = Field(..., description="Revenue at risk * action recovery probability in INR")
    estimated_recovery_probability: float = Field(..., ge=0.0, le=1.0, description="Effective recovery probability")
    friction_level: str = Field(..., description="Customer friction level ('LOW', 'MEDIUM', 'HIGH')")
    friction_deduction: float = Field(default=0.0)
    action_cost: float = Field(default=0.0)
    risk_penalty: float = Field(default=0.0)
    value_score: float = Field(default=0.0)
    is_eligible: bool = Field(default=True)
    rejection_reason: Optional[str] = Field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value if hasattr(self.action, "value") else str(self.action),
            "score": round(self.score, 1),
            "expected_recovery_value": round(self.expected_recovery_value, 2),
            "estimated_recovery_probability": round(self.estimated_recovery_probability, 2),
            "friction_level": self.friction_level,
            "friction_deduction": round(self.friction_deduction, 1),
            "action_cost": round(self.action_cost, 1),
            "risk_penalty": round(self.risk_penalty, 1),
            "value_score": round(self.value_score, 1),
            "is_eligible": self.is_eligible,
            "rejection_reason": self.rejection_reason,
        }


def compute_effective_action_probability(
    action: RecoveryAction,
    context: AIDecisionContext,
    ai_diagnosis: Optional[AIDiagnosisResult] = None
) -> float:
    """
    Computes calibrated action-specific recovery probability:
    Combines the starting assumption with contextual purchase intent, customer history,
    and the AI diagnosis confidence.
    """
    base_prob = ACTION_BASE_PROBABILITIES.get(action, 0.10)
    if action == RecoveryAction.NO_ACTION:
        return ESTIMATED_ACTION_RECOVERY_PROB_NO_ACTION

    # Scale base probability by purchase intent (0-100)
    intent_factor = max(0.2, min(1.3, 0.5 + (context.purchase_intent_score / 100.0) * 0.7))
    
    # Customer history factor (repeat buyers recover faster on personalized actions)
    history_factor = 1.0
    if context.previous_purchases >= 1:
        if action in (RecoveryAction.PERSONALIZED_REMINDER, RecoveryAction.CHECKOUT_REMINDER):
            history_factor = 1.10
    else:
        # First time buyer: slightly lower response for high-pressure payment links
        if action == RecoveryAction.PAYMENT_LINK:
            history_factor = 0.92

    # Blend with AI diagnosis probability if available
    ai_blend_factor = 1.0
    if ai_diagnosis:
        # If AI specifically recommended this action, give confidence boost
        if ai_diagnosis.recommended_action == action:
            ai_blend_factor = 1.05
        # Modulate slightly by AI recovery probability
        ai_prob = ai_diagnosis.recovery_probability
        calibrated = (base_prob * intent_factor * history_factor * 0.75) + (ai_prob * 0.25 * ai_blend_factor)
    else:
        calibrated = base_prob * intent_factor * history_factor

    # Bound strictly between 0.05 and 0.98
    return round(float(min(0.98, max(0.05, calibrated))), 2)


def score_single_action(
    action: RecoveryAction,
    context: AIDecisionContext,
    ai_diagnosis: Optional[AIDiagnosisResult] = None,
    policy: Optional[RecoveryPolicy] = None
) -> ScoredAction:
    """
    Calculates Action Score = Expected Recovery Value − Customer Friction − Action Cost − Risk Penalty.
    Normalizes the result to a 0–100 scale.
    """
    metrics = ACTION_FRICTION_METRICS.get(action, {
        "level": "MEDIUM",
        "base_friction": 15.0,
        "base_cost": 5.0,
    })

    friction_level = metrics["level"]
    friction_deduction = float(metrics["base_friction"])
    action_cost = float(metrics["base_cost"])
    risk_penalty = 0.0

    # 1. Effective Action Recovery Probability & Expected Recovery Value
    effective_prob = compute_effective_action_probability(action, context, ai_diagnosis)
    revenue_at_risk = float(context.revenue_at_risk or context.cart_value or 0.0)
    expected_recovery_val = round(revenue_at_risk * effective_prob, 2)

    # 2. Case: NO_ACTION scoring
    if action == RecoveryAction.NO_ACTION:
        # If cart is negligible (< 100) or low intent (< 30), NO_ACTION is highly favorable
        if revenue_at_risk <= 100.0 or context.purchase_intent_score < 30.0 or context.risk_score < 30.0:
            final_score = 85.0 - (context.purchase_intent_score * 0.5)
        else:
            # High value/intent cart means taking no action is heavily penalized
            final_score = max(5.0, 45.0 - (context.purchase_intent_score * 0.4) - min(25.0, expected_recovery_val / 200.0))
        
        final_score = max(0.0, min(100.0, final_score))
        return ScoredAction(
            action=action,
            score=round(final_score, 1),
            expected_recovery_value=expected_recovery_val,
            estimated_recovery_probability=effective_prob,
            friction_level="LOW",
            friction_deduction=0.0,
            action_cost=0.0,
            risk_penalty=0.0,
            value_score=0.0,
            is_eligible=True,
        )

    # 3. Active Interventions (CHECKOUT_REMINDER, PERSONALIZED_REMINDER, PAYMENT_LINK, DELAYED_FOLLOW_UP)
    # Value Score: Combines base probability, intent, and monetary magnitude
    val_magnitude_score = min(25.0, math.log10(max(10.0, revenue_at_risk)) * 6.5)
    prob_score = effective_prob * 50.0
    intent_score_component = (context.purchase_intent_score / 100.0) * 20.0
    value_score = prob_score + val_magnitude_score + intent_score_component

    # 4. Contextual Friction Adjustments
    if action == RecoveryAction.PERSONALIZED_REMINDER:
        if context.previous_purchases >= 1 or context.customer_lifetime_value > 3000.0:
            # Familiar customer welcomes personalization: reduce friction
            friction_deduction = max(3.0, friction_deduction - 5.0)
        elif context.previous_purchases == 0:
            # Cold customer with no history: personalization feels unnatural / friction up
            friction_deduction += 4.0
            risk_penalty += 3.0

    elif action == RecoveryAction.PAYMENT_LINK:
        # High friction action
        if context.previous_purchases == 0:
            # Low history + cold user: higher risk penalty for pushy payment link
            risk_penalty += 8.0
        if context.purchase_intent_score < 60.0:
            # Low intent for instant pay link is overly aggressive
            risk_penalty += 10.0
        if revenue_at_risk < 500.0:
            # Overkill for small baskets
            risk_penalty += 6.0


    elif action == RecoveryAction.CHECKOUT_REMINDER:
        # Balanced, non-intrusive standard reminder
        if context.purchase_intent_score >= 50.0:
            friction_deduction = max(4.0, friction_deduction - 4.0)

    elif action == RecoveryAction.DELAYED_FOLLOW_UP:
        # Ideal for medium intent / exploratory sessions
        if 35.0 <= context.purchase_intent_score <= 65.0:
            value_score += 8.0
        elif context.purchase_intent_score > 80.0:
            # High intent suffers because delay loses momentum
            risk_penalty += 10.0

    # 5. Integrate AI recommendation alignment bonus
    ai_alignment_bonus = 0.0
    if ai_diagnosis and ai_diagnosis.recommended_action == action:
        ai_alignment_bonus = 4.0 * ai_diagnosis.recommendation_confidence

    # 6. Final Score Calculation & Clamping
    raw_score = (
        value_score
        - friction_deduction
        - action_cost
        - risk_penalty
        + ai_alignment_bonus
    )
    
    # Scale and clamp to [0.0, 100.0]
    final_score = round(max(0.0, min(100.0, raw_score)), 1)

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


def score_all_candidate_actions(
    context: AIDecisionContext,
    eligible_actions: List[RecoveryAction],
    ai_diagnosis: Optional[AIDiagnosisResult] = None,
    policy: Optional[RecoveryPolicy] = None
) -> List[ScoredAction]:
    """
    Scores all candidate actions and returns a list sorted by descending final score.
    """
    scored_list = []
    for action in eligible_actions:
        scored = score_single_action(
            action=action,
            context=context,
            ai_diagnosis=ai_diagnosis,
            policy=policy,
        )
        scored_list.append(scored)

    # Sort descending by decision score
    scored_list.sort(key=lambda x: x.score, reverse=True)
    return scored_list


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
