import uvicorn
import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from app.core.config import settings

    print(f"[*] Starting {settings.PROJECT_NAME} on http://0.0.0.0:{settings.PORT}")
    print(f"[*] Interactive Swagger UI: http://localhost:{settings.PORT}/docs")
    print(f"[*] Health check: http://localhost:{settings.PORT}/api/health")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
