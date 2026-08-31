import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.db import get_db
from app.schemas.health import HealthResponse, ServiceStatus
from app.services.payments import payments_service
from app.services.ai_agent import ai_service

router = APIRouter()


@router.get("", response_model=HealthResponse, summary="System Health Check")
@router.get("/", response_model=HealthResponse, include_in_schema=False)
def check_health(db: Session = Depends(get_db)):
    """
    Health check returning status of Backend, Database, OpenAI, and Razorpay configuration.
    """
    services = {}

    # Database Check
    db_status = "healthy"
    db_latency = None
    db_details = {"engine": db.bind.name if db.bind else "unknown"}
    try:
        t0 = time.perf_counter()
        db.execute(text("SELECT 1"))
        db_latency = round((time.perf_counter() - t0) * 1000, 2)
    except Exception as e:
        db_status = "degraded"
        db_details["error"] = str(e)

    services["database"] = ServiceStatus(
        status=db_status,
        latency_ms=db_latency,
        details=db_details,
    )

    # Razorpay Status
    services["razorpay"] = ServiceStatus(
        status="configured" if payments_service.is_configured() else "placeholder_mode",
        details={
            "mode": "live" if payments_service.is_configured() else "test_mock",
            "currency": settings.RAZORPAY_CURRENCY,
        },
    )

    # OpenAI Status
    services["openai"] = ServiceStatus(
        status="configured" if ai_service.is_configured() else "placeholder_mode",
        details={
            "model": settings.OPENAI_MODEL,
            "mode": "live" if ai_service.is_configured() else "stub_mock",
        },
    )

    # Backend
    services["backend"] = ServiceStatus(
        status="healthy",
        latency_ms=0.5,
        details={"version": settings.VERSION, "env": settings.ENVIRONMENT},
    )

    return HealthResponse(
        status="ok" if db_status == "healthy" else "degraded",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        services=services,
    )
