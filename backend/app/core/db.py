import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def get_engine():
    db_url = settings.DATABASE_URL
    connect_args = {}

    # If sqlite is used
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        # Test connection briefly
        with engine.connect() as conn:
            pass
        return engine
    except Exception as e:
        if settings.USE_SQLITE_FALLBACK and settings.ENVIRONMENT == "development":
            logger.warning(
                f"PostgreSQL connection failed ({e}). Falling back to SQLite for local development: {settings.SQLITE_FALLBACK_URL}"
            )
            fallback_engine = create_engine(
                settings.SQLITE_FALLBACK_URL,
                connect_args={"check_same_thread": False},
                pool_pre_ping=True,
            )
            return fallback_engine
        raise e


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
