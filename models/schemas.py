from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from backend.models.notice import NoticeStructuredData

class UploadResponse(BaseModel):
    status: str = Field("success", description="Status of the upload processing, e.g., 'success' or 'error'")
    filename: str = Field(..., description="Original name of the uploaded document")
    notice_data: NoticeStructuredData = Field(..., description="Structured extracted fields conforming to Day 2 schema")
    processing_stages: List[str] = Field(
        default=[
            "Uploading document",
            "Reading document",
            "Extracting information",
            "Identifying notice type",
            "Building notice summary"
        ],
        description="Discrete stages completed during document analysis"
    )
    extracted_text: Optional[str] = Field(default="", description="Extracted raw text content if applicable")
    ai_response: Optional[str] = Field(default="", description="Plain-language notice overview")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional document processing metadata")

class ErrorResponse(BaseModel):
    status: str = "error"
    error: str = Field(..., description="Detailed error description")
    code: Optional[int] = Field(500, description="HTTP or error code")

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "CivicOps Backend"
    gemini_configured: bool
    adk_status: Dict[str, Any]
