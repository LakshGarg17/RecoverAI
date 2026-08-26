import sys
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Allow importing backend configuration if database/ is executed directly or as a package
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from app.core.config import settings
    from app.core.db import Base, engine, SessionLocal, get_db
except ImportError:
    # Fallback to direct environment variables if standalone
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class FallbackSettings(BaseSettings):
        DATABASE_URL: str = "sqlite:///./recoverai_dev.db"
        model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    settings = FallbackSettings()
    Base = declarative_base()
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_db() -> Generator[Session, None, None]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


def init_db(drop_all: bool = False):
    """Create all tables defined in models. Optionally drop them first."""
    from database.models import Customer, Transaction, RecoveryCase  # noqa: F401
    try:
        from app.models.user import User  # noqa: F401
    except ImportError:
        pass

    if drop_all:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


__all__ = ["engine", "SessionLocal", "Base", "get_db", "init_db", "settings"]
