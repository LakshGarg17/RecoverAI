import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RecoverAI Autonomous Payment Recovery Agent"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    API_V1_STR: str = "/api/v1"

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [v]
        elif isinstance(v, (list, tuple)):
            return [str(i) for i in v]
        return ["*"]

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/recoverai"
    # Fallback to local SQLite if Postgres is not reachable in dev
    USE_SQLITE_FALLBACK: bool = True
    SQLITE_FALLBACK_URL: str = "sqlite:///./recoverai_dev.db"

    # AI Configuration (OpenAI API)
    OPENAI_API_KEY: str = "sk-placeholder-openai-key-your-key-here"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Razorpay Configuration (Test Mode)
    RAZORPAY_KEY_ID: str = "rzp_test_placeholder_key_id"
    RAZORPAY_KEY_SECRET: str = "placeholder_secret_key_here"
    RAZORPAY_CURRENCY: str = "INR"
    RAZORPAY_WEBHOOK_SECRET: str = "placeholder_webhook_secret"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
