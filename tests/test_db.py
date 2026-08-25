import pytest
from app.models.user import User, RecoveryCase
from app.core.db import SessionLocal, Base, engine


def test_db_models_creation():
    """Verify models instantiate and commit properly."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Create test user
        user = User(
            email="test_pilot@recoverai.io",
            full_name="Pilot Tester",
            company_name="Acme Recovery"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.email == "test_pilot@recoverai.io"

        # Cleanup
        db.delete(user)
        db.commit()
    finally:
        db.close()
