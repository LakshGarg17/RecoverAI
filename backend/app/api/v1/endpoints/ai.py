from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.schemas.ai import AIAnalysisRequest, AIAnalysisResponse
from app.services.ai_agent import ai_service
from ai.schemas import DiagnoseEventRequest, DiagnoseEventResponse
from ai.diagnosis import ai_diagnosis_agent
from database.ai_decisions import save_ai_decision, get_decision_by_event_id

router = APIRouter()


@router.post(
    "/diagnose",
    response_model=DiagnoseEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Diagnose Event and Recommend Recovery Action (Day 4)",
    description="Analyzes checkout abandonment using AI, determines root cause, estimates recovery probability, and recommends least-intrusive action."
)
async def diagnose_event_endpoint(
    request: DiagnoseEventRequest,
    db: Session = Depends(get_db)
):
    """
    Diagnoses an e-commerce recovery event:
    1. Fetches event telemetry and customer history
    2. Runs Day 3 deterministic risk engine
    3. Invokes LLM diagnosis agent with structured outputs
    4. Validates outputs and computes Expected Recovery Value
    5. Persists decision in database audit trail
    """
    try:
        event_payload = request.event_data if request.event_data is not None else request.event_id
        if not event_payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'event_id' or 'event_data' must be provided in request payload."
            )

        diagnosis_response = await ai_diagnosis_agent.diagnose_event(event_payload)

        # Persist decision record for auditability
        try:
            decision_dict = diagnosis_response.model_dump()
            save_ai_decision(db, decision_dict)
        except Exception as db_err:
            # Non-blocking log if DB persistence fails in ephemeral dev run
            pass

        return diagnosis_response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Diagnosis Agent failed: {str(e)}"
        )


@router.get(
    "/decisions/{event_id}",
    summary="Get Historical AI Decision for Event",
    description="Fetches the stored audit-trail AI decision for a given event ID."
)
def get_event_decision(event_id: str, db: Session = Depends(get_db)):
    record = get_decision_by_event_id(db, event_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No decision found for event_id '{event_id}'."
        )
    return record.to_dict()


@router.post("/analyze", response_model=AIAnalysisResponse, summary="Analyze Invoice Risk & Strategy")
async def analyze_invoice(request: AIAnalysisRequest):
    """
    Legacy Day 1 endpoint: Evaluate overdue invoice, predict churn risk, and suggest recovery communication strategy.
    """
    try:
        response = await ai_service.analyze_invoice_risk(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Agent failed: {str(e)}")
