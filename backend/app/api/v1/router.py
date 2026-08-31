from fastapi import APIRouter
from app.api.v1.endpoints import health, payments, ai, decision

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, prefix="/health", tags=["Health"])
api_v1_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_v1_router.include_router(ai.router, prefix="/ai", tags=["AI Agent"])
api_v1_router.include_router(decision.router, prefix="/decision", tags=["Recovery Decision Agent"])

