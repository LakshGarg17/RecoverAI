import json
import logging
import mimetypes
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

import google.generativeai as genai
from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.models.notice import NoticeStructuredData

logger = logging.getLogger("civicops.document_agent")

DEFAULT_FALLBACK_DATA: Dict[str, Any] = {
    "notice_type": "Not found",
    "issuing_authority": "Not found",
    "department": "Not found",
    "reference_number": "Not found",
    "citizen_name": "Not found",
    "property_id": "Not found",
    "amount": "Not found",
    "issue": "Not found",
    "deadline": "Not found",
    "required_action": "Not found",
    "mentioned_documents": []
}

DOCUMENT_EXTRACTION_PROMPT = """You are CivicOps Document Intelligence Agent. Your ONLY job is to read and accurately extract key information from this uploaded civic paperwork / government notice into a structured JSON object.

Extract EXACTLY the following fields:
- "notice_type": Type of notice (e.g. "Property Tax Delinquency Notice", "Plan Check Correction Notice", "Parking Citation", "Jury Summons")
- "issuing_authority": The main government entity or agency (e.g. "County of Kings", "City of Oakridge", "Department of Finance")
- "department": The specific division or bureau (e.g. "Office of the Tax Collector", "Department of Building Inspection")
- "reference_number": Any case number, citation number, account number, or reference identifier
- "citizen_name": Full name of the citizen, property owner, or recipient named
- "property_id": Parcel APN, address, vehicle plate/VIN, or permit ID referenced
- "amount": Monetary amount owed, disputed, or billed with currency symbol (e.g. "$4,911.25")
- "issue": Concise plain-language description of why this notice was issued and what violation/delinquency/requirement occurred
- "deadline": Explicit statutory due date or response deadline
- "required_action": Concrete immediate steps required from the citizen
- "mentioned_documents": A JSON array of any specific proofs, forms, receipts, or documents explicitly mentioned that the citizen must submit or have (e.g. ["Dispute Form TC-409", "Proof of previous payment", "Identity proof"])

CRITICAL ANTI-HALLUCINATION RULES:
1. If any field is NOT explicitly mentioned or cannot be confidently extracted from the document, set its value to the exact string "Not found".
2. NEVER guess, assume, or hallucinate missing information.
3. For "mentioned_documents", if no specific documents or forms are requested, return an empty array [].
4. Output MUST be valid JSON only. Do not include any introductory remarks, markdown fences (such as ```json), or trailing comments.

Example output format for a document where citizen name and property id were not mentioned:
{
  "notice_type": "Parking Violation Notice",
  "issuing_authority": "City of Metropolis",
  "department": "Department of Transportation",
  "reference_number": "PV-99120",
  "citizen_name": "Not found",
  "property_id": "Not found",
  "amount": "$75.00",
  "issue": "Vehicle parked in street cleaning zone during restricted hours",
  "deadline": "December 15, 2024",
  "required_action": "Pay citation online or request administrative review within 21 days",
  "mentioned_documents": ["Citation Notice", "Proof of valid residential parking permit"]
}
"""

class DocumentAgent:
    """
    Document Intelligence Agent for CivicOps.
    Processes government paperwork (PDF, JPG, PNG, TXT) using Gemini multimodal capabilities
    and extracts structured notice information according to a rigorous JSON schema.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name or GEMINI_MODEL
        self._model = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.warning("DocumentAgent: GEMINI_API_KEY is not configured. Running in mock/offline mode.")
            return

        try:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
            logger.info(f"DocumentAgent initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"DocumentAgent failed to initialize GenerativeModel: {e}", exc_info=True)
            self._model = None

    def _determine_mime_type(self, file_path: Path) -> str:
        ext = file_path.suffix.lower()
        mapping = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".txt": "text/plain",
        }
        if ext in mapping:
            return mapping[ext]
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"

    def clean_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        """
        Defensively parses raw LLM output into a structured dictionary conforming to NoticeStructuredData.
        Strips markdown fences, extracts JSON blocks, and defaults missing/invalid fields to 'Not found'.
        """
        if not raw_text or not raw_text.strip():
            logger.warning("Empty raw text received for JSON parsing. Returning fallback.")
            return dict(DEFAULT_FALLBACK_DATA)

        text = raw_text.strip()

        # Strip markdown code blocks e.g. ```json ... ``` or ``` ... ```
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

        # If there's surrounding text, extract the innermost or outermost JSON object
        json_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                logger.warning(f"Parsed JSON is not a dictionary: {parsed}")
                return dict(DEFAULT_FALLBACK_DATA)

            # Ensure all required keys exist and normalize 'None' or empty strings to 'Not found'
            cleaned: Dict[str, Any] = {}
            for key, default_val in DEFAULT_FALLBACK_DATA.items():
                val = parsed.get(key)
                if key == "mentioned_documents":
                    if isinstance(val, list):
                        # Filter out empty or non-string entries
                        cleaned[key] = [str(item).strip() for item in val if item and str(item).strip()]
                    elif isinstance(val, str) and val.strip() and val.strip().lower() != "not found":
                        cleaned[key] = [val.strip()]
                    else:
                        cleaned[key] = []
                else:
                    if val is None or (isinstance(val, str) and not val.strip()):
                        cleaned[key] = "Not found"
                    else:
                        cleaned[key] = str(val).strip()

            return cleaned
        except Exception as e:
            logger.error(f"Failed to parse LLM JSON output: {e}. Raw content: {raw_text[:200]}")
            return dict(DEFAULT_FALLBACK_DATA)

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Reads an uploaded document (PDF, JPG, PNG, TXT) using Gemini multimodal API
        and returns structured JSON data conforming to NoticeStructuredData.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document file not found at: {file_path}")

        mime_type = self._determine_mime_type(path)
        logger.info(f"Processing document: {path.name} (MIME: {mime_type})")

        # Mock / Demo fallback if API key is not configured
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.info("Using simulated fallback response (GEMINI_API_KEY not configured).")
            return self._generate_simulated_response(path)

        if not self._model:
            self._initialize_client()

        if not self._model:
            logger.warning("Gemini model unavailable. Falling back to default structure.")
            return dict(DEFAULT_FALLBACK_DATA)

        try:
            # Build multimodal content parts
            with open(path, "rb") as f:
                file_bytes = f.read()

            if mime_type == "text/plain":
                try:
                    text_content = file_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    text_content = file_bytes.decode("latin-1", errors="replace")
                content_payload = [
                    DOCUMENT_EXTRACTION_PROMPT,
                    f"\n\n--- DOCUMENT CONTENT ({path.name}) ---\n{text_content}\n--- END OF DOCUMENT ---"
                ]
            else:
                # Multimodal binary part (PDF, JPG, PNG)
                part = {
                    "mime_type": mime_type,
                    "data": file_bytes
                }
                content_payload = [DOCUMENT_EXTRACTION_PROMPT, part]

            response = self._model.generate_content(content_payload)
            if not response or not response.text:
                logger.warning("Gemini returned empty response for document extraction.")
                return dict(DEFAULT_FALLBACK_DATA)

            return self.clean_and_parse_json(response.text)

        except Exception as e:
            logger.error(f"Error calling Gemini multimodal API in DocumentAgent: {e}", exc_info=True)
            # Safe fallback without crashing
            return dict(DEFAULT_FALLBACK_DATA)

    def _generate_simulated_response(self, path: Path) -> Dict[str, Any]:
        """
        Generates realistic structured sample responses for local testing when API key is missing.
        """
        lower_name = path.name.lower()
        if "tax" in lower_name:
            return {
                "notice_type": "Property Tax Delinquency Notice",
                "issuing_authority": "County of Kings",
                "department": "Office of the Tax Collector",
                "reference_number": "APN-4920-038-012",
                "citizen_name": "Not found",
                "property_id": "Parcel 4920-038-012",
                "amount": "$4,911.25",
                "issue": "Unpaid second installment property tax for fiscal year 2023-2024",
                "deadline": "November 30, 2024",
                "required_action": "Pay delinquent balance online or submit Dispute Form TC-409 with supporting records.",
                "mentioned_documents": [
                    "Dispute Form TC-409",
                    "Proof of prior payment / canceled check",
                    "Title / deed verification"
                ]
            }
        elif "permit" in lower_name or "building" in lower_name:
            return {
                "notice_type": "Plan Check Correction Notice",
                "issuing_authority": "City of Oakridge",
                "department": "Department of Building Inspection",
                "reference_number": "BLD-2024-88412",
                "citizen_name": "Not found",
                "property_id": "Permit Application #BLD-2024-88412",
                "amount": "$185.00",
                "issue": "Plan check corrections required for rooftop solar photovoltaic installation",
                "deadline": "Within 60 calendar days",
                "required_action": "Revise structural rafter calculations, provide AC disconnect location, and resubmit plans with re-review fee.",
                "mentioned_documents": [
                    "Revised Structural Calculations (Stamped by PE)",
                    "Single Line Electrical Diagram",
                    "AC Disconnect Specification Sheet"
                ]
            }
        else:
            return {
                "notice_type": "Civic Notice",
                "issuing_authority": "Municipal Administrative Agency",
                "department": "Records & Compliance Bureau",
                "reference_number": "REF-2024-001",
                "citizen_name": "Not found",
                "property_id": "Not found",
                "amount": "Not found",
                "issue": "Government paperwork submitted for processing",
                "deadline": "Not found",
                "required_action": "Review document contents and contact issuing agency if necessary.",
                "mentioned_documents": []
            }
