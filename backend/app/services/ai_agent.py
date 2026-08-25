import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.schemas.ai import AIAnalysisRequest, AIAnalysisResponse

logger = logging.getLogger(__name__)


class AIAgentService:
    """Service stub for Autonomous Payment Recovery decisions using OpenAI structured outputs."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL

    def is_configured(self) -> bool:
        """Check if valid OpenAI key is provided."""
        return bool(self.api_key) and not self.api_key.startswith("sk-placeholder")

    async def analyze_invoice_risk(self, request: AIAnalysisRequest) -> AIAnalysisResponse:
        """
        Analyze payment delay risk and recommend recovery action.
        Returns structured AI decision.
        """
        if not self.is_configured():
            logger.info("OpenAI API in mock/stub mode. Returning simulated decision.")
            # Deterministic mock rule for testing Day 1
            if request.overdue_days > 30:
                risk = "high"
                action = "escalate_to_human_or_sms"
                channel = "sms"
                text = f"Urgent: Payment of {request.currency} {request.amount} for {request.customer_name} is overdue by {request.overdue_days} days. Please settle immediately."
                confidence = 0.88
            else:
                risk = "low"
                action = "friendly_reminder"
                channel = "email"
                text = f"Hi {request.customer_name}, this is a gentle reminder regarding invoice amount {request.currency} {request.amount} ({request.overdue_days} days overdue)."
                confidence = 0.95

            return AIAnalysisResponse(
                risk_level=risk,
                recommended_action=action,
                suggested_channel=channel,
                personalized_draft=text,
                confidence_score=confidence,
            )

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        prompt = (
            f"Analyze overdue payment for {request.customer_name}. "
            f"Amount: {request.currency} {request.amount}, Overdue: {request.overdue_days} days. "
            f"Previous context: {request.previous_communications}"
        )

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are RecoverAI, an autonomous agent recovering failed and overdue B2B/B2C SaaS payments.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        # Parse output when live key is attached
        import json
        data = json.loads(response.choices[0].message.content or "{}")
        return AIAnalysisResponse(
            risk_level=data.get("risk_level", "medium"),
            recommended_action=data.get("recommended_action", "friendly_reminder"),
            suggested_channel=data.get("suggested_channel", "email"),
            personalized_draft=data.get("personalized_draft", ""),
            confidence_score=data.get("confidence_score", 0.9),
        )


ai_service = AIAgentService()
