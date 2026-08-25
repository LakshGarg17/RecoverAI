from sqlalchemy import Column, String, Boolean
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    company_name = Column(String(255), nullable=True)


class RecoveryCase(BaseModel):
    """Placeholder model for payment recovery tracking in later days."""
    __tablename__ = "recovery_cases"

    invoice_id = Column(String(100), unique=True, index=True, nullable=False)
    customer_email = Column(String(255), index=True, nullable=False)
    amount = Column(String(50), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, recovered, failed, abandoned
    strategy_used = Column(String(100), nullable=True)
