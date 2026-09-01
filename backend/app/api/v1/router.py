from fastapi import APIRouter
from app.api.v1.endpoints import (

    health,
    payments,
    ai,
    decision,
    guardrails,
    execution,
    webhooks,
    recovery,
    dashboard,
    transactions,
    audit,
    analytics,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, prefix="/health", tags=["Health"])
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["Revenue Recovery Analytics"])
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["Proof-of-Recovery & ROI Analytics"])
api_v1_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_v1_router.include_router(ai.router, prefix="/ai", tags=["AI Agent"])
api_v1_router.include_router(decision.router, prefix="/decision", tags=["Recovery Decision Agent"])
api_v1_router.include_router(guardrails.router, prefix="/guardrails", tags=["Guardrail Engine"])
api_v1_router.include_router(execution.router, prefix="/execution", tags=["Recovery Execution Layer"])
api_v1_router.include_router(webhooks.router, prefix="/webhooks", tags=["Razorpay Webhooks"])
api_v1_router.include_router(recovery.router, prefix="/recovery", tags=["Autonomous Recovery Pipeline"])
api_v1_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions & Executions"])
api_v1_router.include_router(audit.router, prefix="/audit", tags=["Guardrail Audit Log"])





