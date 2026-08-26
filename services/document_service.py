import logging
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Tuple
from fastapi import UploadFile, HTTPException

from backend.config import UPLOAD_DIR, MAX_FILE_SIZE_MB
from backend.agents.document_agent import DocumentAgent
from backend.models.notice import NoticeStructuredData
from backend.models.schemas import UploadResponse

logger = logging.getLogger("civicops.document_service")

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "text/plain"
}

PROCESSING_STAGES = [
    "Uploading document",
    "Reading document",
    "Extracting information",
    "Identifying notice type",
    "Building notice summary"
]

class DocumentService:
    """
    Service responsible for document ingestion, local disk persistence,
    validation, and routing to the DocumentAgent.
    """

    def __init__(self, document_agent: DocumentAgent = None):
        self.agent = document_agent or DocumentAgent()

    def validate_file(self, filename: str, content_type: str = "", file_size: int = 0) -> None:
        """
        Validates file extension, empty status, and maximum allowed file size.
        """
        if not filename:
            raise HTTPException(status_code=400, detail="No filename provided in upload.")

        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(sorted(list(ALLOWED_EXTENSIONS)))
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}'. Supported types are: {allowed_list}"
            )

        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum limit of {MAX_FILE_SIZE_MB}MB."
            )

    async def save_uploaded_file(self, upload_file: UploadFile) -> Tuple[Path, bytes]:
        """
        Reads and saves the uploaded file locally to UPLOAD_DIR.
        """
        content_bytes = await upload_file.read()
        if len(content_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        self.validate_file(
            filename=upload_file.filename,
            content_type=upload_file.content_type or "",
            file_size=len(content_bytes)
        )

        safe_prefix = uuid.uuid4().hex[:8]
        clean_name = Path(upload_file.filename).name.replace(" ", "_")
        target_path = UPLOAD_DIR / f"{safe_prefix}_{clean_name}"

        try:
            with open(target_path, "wb") as f:
                f.write(content_bytes)
            logger.info(f"Saved uploaded file to: {target_path}")
        except Exception as e:
            logger.error(f"Failed to write uploaded file to disk: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to save uploaded file locally: {str(e)}")

        return target_path, content_bytes

    async def process_upload(self, upload_file: UploadFile) -> UploadResponse:
        """
        Orchestrates full upload pipeline: file save -> DocumentAgent -> NoticeStructuredData -> UploadResponse.
        """
        target_path, content_bytes = await self.save_uploaded_file(upload_file)

        try:
            # Invoke DocumentAgent
            extracted_dict = self.agent.process_document(str(target_path))
            notice_data = NoticeStructuredData(**extracted_dict)

            # Plain-language overview for display
            overview_text = (
                f"**Notice Type:** {notice_data.notice_type}\n"
                f"**Authority:** {notice_data.issuing_authority} ({notice_data.department})\n"
                f"**Reference #:** {notice_data.reference_number}\n"
                f"**Amount:** {notice_data.amount}\n"
                f"**Deadline:** {notice_data.deadline}\n\n"
                f"**Core Issue:**\n{notice_data.issue}\n\n"
                f"**Required Action:**\n{notice_data.required_action}"
            )

            return UploadResponse(
                status="success",
                filename=upload_file.filename,
                notice_data=notice_data,
                processing_stages=PROCESSING_STAGES,
                extracted_text=notice_data.issue,
                ai_response=overview_text,
                metadata={
                    "file_size_bytes": len(content_bytes),
                    "saved_path": str(target_path),
                    "content_type": upload_file.content_type or self.agent._determine_mime_type(target_path)
                }
            )
        except Exception as e:
            logger.error(f"Error executing DocumentAgent pipeline: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")
