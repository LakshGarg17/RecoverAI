"""
RecoverAI AI Package Root
Exposes diagnosis agent, schemas, prompts, and context builders.
"""

from ai.schemas import (
    DiagnosisCategory,
    RecoveryAction,
    PriorityTier,
    AIDiagnosisResult,
    AIDecisionContext,
    DiagnoseEventRequest,
    DiagnoseEventResponse,
)
from ai.prompts import SYSTEM_PROMPT, build_diagnosis_user_prompt
from ai.diagnosis import (
    AIDiagnosisAgent,
    ai_diagnosis_agent,
    build_ai_decision_context,
    generate_deterministic_fallback,
    get_processed_dataset,
)

__all__ = [
    "DiagnosisCategory",
    "RecoveryAction",
    "PriorityTier",
    "AIDiagnosisResult",
    "AIDecisionContext",
    "DiagnoseEventRequest",
    "DiagnoseEventResponse",
    "SYSTEM_PROMPT",
    "build_diagnosis_user_prompt",
    "AIDiagnosisAgent",
    "ai_diagnosis_agent",
    "build_ai_decision_context",
    "generate_deterministic_fallback",
    "get_processed_dataset",
]
