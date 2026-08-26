import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("civicops.config")

# Load .env from project root or backend folder
env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent / ".env"

load_dotenv(dotenv_path=env_path)

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Server Configuration
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Storage Configuration (Local Disk Storage)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(Path(__file__).resolve().parent / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

# Google ADK Configuration & Sanity Check
def initialize_adk() -> dict:
    """
    Initializes and verifies Google ADK configuration.
    ADK will be wired into multi-agent workflows in subsequent milestones.
    """
    adk_status = {
        "installed": False,
        "package": None,
        "message": "ADK setup not verified"
    }
    try:
        import adk  # type: ignore
        adk_status["installed"] = True
        adk_status["package"] = "adk"
        adk_status["message"] = "Google ADK package loaded successfully"
        logger.info("Google ADK initialized successfully.")
    except ImportError:
        try:
            import google_adk  # type: ignore
            adk_status["installed"] = True
            adk_status["package"] = "google_adk"
            adk_status["message"] = "Google ADK (google_adk) loaded successfully"
            logger.info("Google ADK (google_adk) initialized successfully.")
        except ImportError:
            adk_status["installed"] = False
            adk_status["message"] = "Google ADK library not found in environment (ready for installation)"
            logger.warning("Google ADK package not found. Agents will be enabled in upcoming milestones.")
    return adk_status

ADK_STATUS = initialize_adk()
