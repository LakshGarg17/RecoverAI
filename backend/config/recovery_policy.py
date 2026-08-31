"""
Merchant Recovery Policy Configuration (Day 5 & Day 6)
Defines configurable merchant-level constraints, thresholds, permissions, and guardrail rules.
Used by both the Decision Engine and the Guardrail Engine.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator


class RecoveryPolicy(BaseModel):
    """
    Merchant-level configurable policy governing autonomous recovery interventions and risk guardrails.
    """
    policy_version: str = Field(
        default="v1.1",
        description="Version identifier of this merchant policy configuration."
    )
    max_recovery_attempts: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Maximum recovery communication attempts allowed per abandoned event/transaction."
    )
    max_contact_attempts: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Alias for max_recovery_attempts for backward compatibility."
    )
    cooldown_minutes: int = Field(
        default=60,
        ge=0,
        description="Minimum quiet time in minutes required between successive recovery attempts."
    )
    minimum_risk_score: float = Field(
        default=60.0,
        ge=0.0,
        le=100.0,
        description="Minimum risk score required to authorize proactive recovery actions."
    )
    minimum_recovery_probability: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Minimum threshold probability required to trigger active outreach."
    )
    minimum_expected_value: float = Field(
        default=100.0,
        ge=0.0,
        description="Minimum expected recovery revenue in INR required to justify action."
    )
    max_transaction_value: float = Field(
        default=100000.0,
        ge=0.0,
        description="Maximum allowable transaction value for autonomous recovery (higher triggers manual review)."
    )
    allow_payment_link: bool = Field(
        default=True,
        description="Whether direct payment links can be generated and dispatched."
    )
    allow_payment_links: bool = Field(
        default=True,
        description="Alias for allow_payment_link."
    )
    allow_personalized_reminder: bool = Field(
        default=True,
        description="Whether AI-personalized messaging is permitted for repeat/VIP buyers."
    )
    allow_personalized_messages: bool = Field(
        default=True,
        description="Alias for allow_personalized_reminder."
    )
    allow_checkout_reminder: bool = Field(
        default=True,
        description="Whether standard checkout reminders are permitted."
    )
    allow_delayed_follow_up: bool = Field(
        default=True,
        description="Whether delayed follow-up reminders are permitted."
    )
    max_customer_contact_frequency_24h: int = Field(
        default=3,
        ge=1,
        description="Maximum cumulative recovery interventions for a single customer in a rolling 24h window."
    )
    high_value_review_threshold: float = Field(
        default=50000.0,
        ge=0.0,
        description="Threshold above which high-value carts with uncertain signals trigger manual review."
    )
    max_customer_friction: str = Field(
        default="HIGH",
        description="Maximum customer friction tolerance ('LOW', 'MEDIUM', 'HIGH')."
    )
    min_cart_value_for_payment_link: float = Field(
        default=150.0,
        ge=0.0,
        description="Minimum cart value required before dispatching high-friction payment links."
    )
    min_intent_for_payment_link: float = Field(
        default=35.0,
        ge=0.0,
        le=100.0,
        description="Minimum purchase intent score required before generating payment links."
    )

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # Sync max_recovery_attempts / max_contact_attempts
            if "max_recovery_attempts" in values and "max_contact_attempts" not in values:
                values["max_contact_attempts"] = values["max_recovery_attempts"]
            elif "max_contact_attempts" in values and "max_recovery_attempts" not in values:
                values["max_recovery_attempts"] = values["max_contact_attempts"]
            
            # Sync allow_payment_link / allow_payment_links
            if "allow_payment_link" in values and "allow_payment_links" not in values:
                values["allow_payment_links"] = values["allow_payment_link"]
            elif "allow_payment_links" in values and "allow_payment_link" not in values:
                values["allow_payment_link"] = values["allow_payment_links"]

            # Sync allow_personalized_reminder / allow_personalized_messages
            if "allow_personalized_reminder" in values and "allow_personalized_messages" not in values:
                values["allow_personalized_messages"] = values["allow_personalized_reminder"]
            elif "allow_personalized_messages" in values and "allow_personalized_reminder" not in values:
                values["allow_personalized_reminder"] = values["allow_personalized_messages"]

        return values

    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary."""
        return self.model_dump()


# Default Merchant Recovery Policy Configuration
DEFAULT_RECOVERY_POLICY: Dict[str, Any] = {
    "policy_version": "v1.1",
    "max_recovery_attempts": 2,
    "max_contact_attempts": 2,
    "cooldown_minutes": 60,
    "minimum_risk_score": 60.0,
    "minimum_recovery_probability": 0.40,
    "minimum_expected_value": 100.0,
    "max_transaction_value": 100000.0,
    "allow_payment_link": True,
    "allow_payment_links": True,
    "allow_personalized_reminder": True,
    "allow_personalized_messages": True,
    "allow_checkout_reminder": True,
    "allow_delayed_follow_up": True,
    "max_customer_contact_frequency_24h": 3,
    "high_value_review_threshold": 50000.0,
    "max_customer_friction": "HIGH",
    "min_cart_value_for_payment_link": 150.0,
    "min_intent_for_payment_link": 35.0,
}


def get_recovery_policy(custom_overrides: Optional[Dict[str, Any]] = None) -> RecoveryPolicy:
    """
    Returns a RecoveryPolicy instance with optional merchant-specific overrides.
    """
    merged = dict(DEFAULT_RECOVERY_POLICY)
    if custom_overrides:
        merged.update(custom_overrides)
    return RecoveryPolicy.model_validate(merged)
