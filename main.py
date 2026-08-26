import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, ADK_STATUS
from backend.models.schemas import UploadResponse, ErrorResponse, HealthResponse
from backend.services.document_service import DocumentService

logger = logging.getLogger("civicops.main")

# Initialize Document Service
document_service = DocumentService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting CivicOps Backend Service (Day 2 Document Agent)...")
    logger.info(f"Gemini Model configured: {GEMINI_MODEL}")
    logger.info(f"ADK Status: {ADK_STATUS['message']}")
    yield
    logger.info("Shutting down CivicOps Backend Service...")

app = FastAPI(
    title="CivicOps API",
    description="Autonomous civic paperwork assistant API (Day 2: Document Intelligence Agent)",
    version="0.2.0",
    lifespan=lifespan
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify backend status, Gemini readiness, and ADK availability.
    """
    is_gemini_ready = bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here")
    return HealthResponse(
        status="ok",
        service="CivicOps Backend",
        gemini_configured=is_gemini_ready,
        adk_status=ADK_STATUS
    )

@app.post("/upload", response_model=UploadResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts an uploaded civic document (PDF, JPG, PNG, TXT), validates it,
    stores it locally, and runs the DocumentAgent to extract structured notice JSON.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided in upload.")

    return await document_service.process_upload(file)
