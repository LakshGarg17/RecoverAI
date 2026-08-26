import pytest
from datetime import datetime
from database.database import SessionLocal, init_db
from database.models import Customer, Transaction, RecoveryCase


@pytest.fixture(scope="module")
def db_session():
    init_db()
    session = SessionLocal()
    yield session
    session.close()


def test_customer_model_crud(db_session):
    """Test creating, reading, updating and deleting a Customer."""
    cust_id = "cust_test_unit_001"
    customer = Customer(
        customer_id=cust_id,
        name="Aditi Sharma",
        email="aditi.sharma.test@recoverai.io",
        total_transactions=5,
        successful_transactions=4,
        failed_transactions=1,
        lifetime_value=12500.50,
        created_at=datetime.utcnow(),
    )
    db_session.add(customer)
    db_session.commit()

    fetched = db_session.query(Customer).filter_by(customer_id=cust_id).first()
    assert fetched is not None
    assert fetched.name == "Aditi Sharma"
    assert fetched.total_transactions == 5
    assert fetched.successful_transactions == 4
    assert fetched.failed_transactions == 1
    assert fetched.lifetime_value == 12500.50
    assert repr(fetched).startswith("<Customer")

    # Cleanup
    db_session.delete(fetched)
    db_session.commit()


def test_transaction_and_recovery_case_relationship(db_session):
    """Test creating Transaction linked to Customer and RecoveryCase linked to Transaction."""
    cust_id = "cust_test_unit_002"
    txn_id = "txn_test_unit_001"
    case_id = "case_test_unit_001"

    customer = Customer(
        customer_id=cust_id,
        name="Vikram Patel",
        email="vikram.patel.test@recoverai.io",
        total_transactions=1,
        successful_transactions=0,
        failed_transactions=1,
        lifetime_value=0.0,
    )
    db_session.add(customer)
    db_session.commit()

    transaction = Transaction(
        transaction_id=txn_id,
        customer_id=cust_id,
        amount=4500.00,
        currency="INR",
        payment_method="UPI",
        status="failed",
        failure_reason="bank_timeout",
        created_at=datetime.utcnow(),
    )
    db_session.add(transaction)
    db_session.commit()

    recovery_case = RecoveryCase(
        case_id=case_id,
        transaction_id=txn_id,
        amount_at_risk=4500.00,
        risk_score=None,
        recovery_probability=None,
        recommended_action=None,
        status="pending",
        attempt_count=0,
        amount_recovered=0.0,
    )
    db_session.add(recovery_case)
    db_session.commit()

    # Query through customer relationships
    queried_customer = db_session.query(Customer).filter_by(customer_id=cust_id).first()
    assert len(queried_customer.transactions) == 1
    assert queried_customer.transactions[0].transaction_id == txn_id
    assert queried_customer.transactions[0].recovery_case is not None
    assert queried_customer.transactions[0].recovery_case.case_id == case_id
    assert queried_customer.transactions[0].recovery_case.amount_at_risk == 4500.00
    assert repr(transaction).startswith("<Transaction")
    assert repr(recovery_case).startswith("<RecoveryCase")

    # Cascade delete test: deleting customer should delete transactions and recovery cases
    db_session.delete(queried_customer)
    db_session.commit()

    assert db_session.query(Transaction).filter_by(transaction_id=txn_id).first() is None
    assert db_session.query(RecoveryCase).filter_by(case_id=case_id).first() is None
