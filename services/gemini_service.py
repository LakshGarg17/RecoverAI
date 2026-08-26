import logging
from typing import Optional
import google.generativeai as genai
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger("civicops.gemini_service")

class GeminiService:
    """
    Service wrapper for Google Gemini API.
    Interacts with the Google Generative AI SDK to translate complex paperwork into plain language.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name or GEMINI_MODEL
        self._model = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.warning("GEMINI_API_KEY is not configured or is a placeholder. API calls will require a valid key.")
            return

        try:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
            logger.info(f"GeminiService initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini GenerativeModel: {e}", exc_info=True)
            self._model = None

    def generate_response(self, prompt: str, document_text: str) -> str:
        """
        Sends prompt and document text to the Gemini API and returns plain text explanation and actions.
        """
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return (
                "⚠️ **Gemini API Key Missing**\n\n"
                "Please configure a valid `GEMINI_API_KEY` in your `.env` file.\n\n"
                "**Simulated Analysis for Document:**\n"
                f"Document text received ({len(document_text)} characters).\n\n"
                "**What this notice means:**\n"
                "- This is a standard civic/government notice requiring attention.\n"
                "- The issuing department requires verification, payment, or corrective action.\n\n"
                "**Recommended Next Steps:**\n"
                "1. Add your real Gemini API key to `.env` to unlock live AI extraction.\n"
                "2. Review deadlines specified in the notice header.\n"
                "3. Gather any supporting identification or referenced case numbers."
            )

        if not self._model:
            # Try re-initializing in case API key was updated
            self._initialize_client()

        if not self._model:
            raise RuntimeError("Gemini model is not initialized. Please verify your GEMINI_API_KEY configuration.")

        full_prompt = (
            f"{prompt}\n\n"
            f"--- START OF DOCUMENT ---\n"
            f"{document_text}\n"
            f"--- END OF DOCUMENT ---"
        )

        try:
            logger.info(f"Sending document ({len(document_text)} chars) to Gemini model {self.model_name}")
            response = self._model.generate_content(full_prompt)
            
            if not response or not response.text:
                logger.warning("Gemini returned an empty response.")
                return "No response could be generated for this document. Please ensure the document is clear and readable."
            
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            raise RuntimeError(f"Gemini API error: {str(e)}")
