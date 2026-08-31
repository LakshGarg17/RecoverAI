"""
Merchant Recovery Policy Configuration (Day 5)
Defines configurable merchant-level constraints, thresholds, and permissions.
Used by the Decision Engine to filter candidate actions and enforce guardrails.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class RecoveryPolicy(BaseModel):
    """
    Merchant-level configurable policy governing autonomous recovery interventions.
    """
    max_contact_attempts: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Maximum recovery communication attempts allowed per abandoned event."
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
    allow_payment_links: bool = Field(
        default=True,
        description="Whether direct payment links can be generated and dispatched."
    )
    allow_personalized_messages: bool = Field(
        default=True,
        description="Whether AI-personalized messaging is permitted for repeat/VIP buyers."
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary."""
        return self.model_dump()


# Default Merchant Recovery Policy Configuration
DEFAULT_RECOVERY_POLICY: Dict[str, Any] = {
    "max_contact_attempts": 2,
    "minimum_recovery_probability": 0.40,
    "minimum_expected_value": 100.0,
    "allow_payment_links": True,
    "allow_personalized_messages": True,
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
