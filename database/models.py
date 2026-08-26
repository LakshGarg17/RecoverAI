import sys
import os
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

# Ensure database and backend paths are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
backend_path = os.path.join(root_dir, "backend")
for path in [root_dir, backend_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

from database.database import Base


class Customer(Base):
    """
    Customer entity representing merchant customers with lifetime transaction metrics.
    """
    __tablename__ = "customers"

    customer_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    total_transactions = Column(Integer, default=0, nullable=False)
    successful_transactions = Column(Integer, default=0, nullable=False)
    failed_transactions = Column(Integer, default=0, nullable=False)
    lifetime_value = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transactions = relationship(
        "Transaction",
        back_populates="customer",
        cascade="all, delete-orphan",
        order_by="Transaction.created_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<Customer {self.customer_id} ({self.name}, LTV: ₹{self.lifetime_value:.2f})>"


class Transaction(Base):
    """
    Transaction record representing payment attempts through various payment gateways & methods.
    """
    __tablename__ = "transactions"

    transaction_id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(
        String(64),
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    payment_method = Column(String(30), nullable=False)  # UPI, CARD, NETBANKING, WALLET
    status = Column(String(30), nullable=False)          # success, failed, pending, abandoned
    failure_reason = Column(String(50), nullable=True)   # bank_decline, insufficient_funds, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    customer = relationship("Customer", back_populates="transactions")
    recovery_case = relationship(
        "RecoveryCase",
        back_populates="transaction",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction {self.transaction_id} (Cust: {self.customer_id}, "
            f"Amt: ₹{self.amount:.2f}, Status: {self.status})>"
        )


class RecoveryCase(Base):
    """
    Autonomous Recovery Case tracking failed payment recovery strategies and lifecycle.
    """
    __tablename__ = "recovery_cases"

    case_id = Column(String(64), primary_key=True, index=True)
    transaction_id = Column(
        String(64),
        ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    amount_at_risk = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=True)               # Filled Day 3/4 by Risk Engine
    recovery_probability = Column(Float, nullable=True)     # Filled Day 3/4 by ML/Risk Engine
    recommended_action = Column(String(100), nullable=True) # Filled Day 3/4 by Strategy Engine
    status = Column(String(50), default="pending", nullable=False)  # pending, in_progress, recovered, failed, abandoned
    attempt_count = Column(Integer, default=0, nullable=False)
    amount_recovered = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    transaction = relationship("Transaction", back_populates="recovery_case")

    def __repr__(self) -> str:
        return (
            f"<RecoveryCase {self.case_id} (Txn: {self.transaction_id}, "
            f"Risk: ₹{self.amount_at_risk:.2f}, Status: {self.status})>"
        )


__all__ = ["Customer", "Transaction", "RecoveryCase"]
