from fastapi import APIRouter, HTTPException
from app.schemas.ai import AIAnalysisRequest, AIAnalysisResponse
from app.services.ai_agent import ai_service

router = APIRouter()


@router.post("/analyze", response_model=AIAnalysisResponse, summary="Analyze Invoice Risk & Strategy")
async def analyze_invoice(request: AIAnalysisRequest):
    """
    Evaluate overdue invoice, predict churn risk, and suggest recovery communication strategy.
    """
    try:
        response = await ai_service.analyze_invoice_risk(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Agent failed: {str(e)}")
