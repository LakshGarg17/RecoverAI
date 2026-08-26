import pytest
from app.models.user import User
from database.database import SessionLocal, Base, engine, init_db


def test_db_models_creation():
    """Verify models instantiate and commit properly."""
    init_db()
    db = SessionLocal()
    try:
        # Create test user
        user = User(
            email="test_pilot@recoverai.io",
            full_name="Pilot Tester",
            company_name="Acme Recovery",
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
