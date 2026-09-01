import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import engine, Base
import app.models  # Ensure all models are registered
from app.api.v1.router import api_v1_router
from app.api.v1.endpoints.health import check_health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist in dev environment
    logger.info(f"Starting {settings.PROJECT_NAME} (env: {settings.ENVIRONMENT})")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schemas verified.")
    except Exception as e:
        logger.warning(f"Could not initialize DB tables on startup: {e}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous AI agent for recovering failed and overdue payments in SaaS and B2B workflows.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware setup for frontend connectivity
origins = settings.BACKEND_CORS_ORIGINS
if isinstance(origins, list):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Versioned API routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

from app.api.v1.endpoints import ai as ai_endpoints
from app.api.v1.endpoints import decision as decision_endpoints
from app.api.v1.endpoints import guardrails as guardrail_endpoints
from app.api.v1.endpoints import execution as execution_endpoints
from app.api.v1.endpoints import webhooks as webhook_endpoints
from app.api.v1.endpoints import recovery as recovery_endpoints

from app.api.v1.endpoints import dashboard as dashboard_endpoints

from app.api.v1.endpoints import transactions as transaction_endpoints
from app.api.v1.endpoints import audit as audit_endpoints
from app.api.v1.endpoints import analytics as analytics_endpoints

app.include_router(ai_endpoints.router, prefix="/api/ai", tags=["AI Agent (Direct Alias)"])
app.include_router(decision_endpoints.router, prefix="/api/decision", tags=["Recovery Decision Agent (Direct Alias)"])
app.include_router(guardrail_endpoints.router, prefix="/api/guardrails", tags=["Guardrail Engine (Direct Alias)"])
app.include_router(execution_endpoints.router, prefix="/api/execution", tags=["Recovery Execution (Direct Alias)"])
app.include_router(webhook_endpoints.router, prefix="/api/webhooks", tags=["Razorpay Webhooks (Direct Alias)"])
app.include_router(recovery_endpoints.router, prefix="/api/recovery", tags=["Autonomous Recovery Pipeline (Direct Alias)"])
app.include_router(dashboard_endpoints.router, prefix="/api/dashboard", tags=["Revenue Recovery Analytics (Direct Alias)"])
app.include_router(analytics_endpoints.router, prefix="/api/analytics", tags=["Proof-of-Recovery & ROI Analytics (Direct Alias)"])
app.include_router(transaction_endpoints.router, prefix="/api/transactions", tags=["Transactions & Executions (Direct Alias)"])
app.include_router(audit_endpoints.router, prefix="/api/audit", tags=["Guardrail Audit Log (Direct Alias)"])






# Top-level Health check endpoints: GET /api/health and GET /health
app.add_api_route(
    "/api/health",
    check_health,
    methods=["GET"],
    tags=["Health"],
    summary="Top-level API Health Check",
)
app.add_api_route(
    "/health",
    check_health,
    methods=["GET"],
    tags=["Health"],
    summary="Root Health Check",
)



@app.get("/", tags=["General"])
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "api_v1": settings.API_V1_STR,
    }
