import pytest
from database.database import SessionLocal, init_db
from database.models import Customer, Transaction, RecoveryCase
from database.seed import generate_seed_data, seed_database


def test_seed_generator_output_counts():
    """Verify generator output counts and types."""
    customers, transactions, recovery_cases = generate_seed_data(
        num_loyal=10,
        num_new=15,
        num_high_val=5,
        num_problematic=10,
        num_standard=20,
        recovery_case_sample_rate=0.5,
    )

    assert len(customers) == 60
    assert len(transactions) > 100
    assert len(recovery_cases) > 0


def test_customer_aggregates_and_integrity():
    """Verify customer aggregate metrics correspond accurately with generated transactions."""
    customers, transactions, recovery_cases = generate_seed_data(
        num_loyal=10,
        num_new=10,
        num_high_val=10,
        num_problematic=10,
        num_standard=10,
    )

    # Group transactions by customer_id
    txn_map = {}
    for t in transactions:
        txn_map.setdefault(t.customer_id, []).append(t)

    for cust in customers:
        c_txns = txn_map.get(cust.customer_id, [])
        assert cust.total_transactions == len(c_txns)

        expected_success = sum(1 for t in c_txns if t.status == "success")
        expected_failed = sum(1 for t in c_txns if t.status == "failed")
        expected_ltv = sum(t.amount for t in c_txns if t.status == "success")

        assert cust.successful_transactions == expected_success
        assert cust.failed_transactions == expected_failed
        assert abs(cust.lifetime_value - round(expected_ltv, 2)) < 0.01

        # Check chronology: customer created_at is <= all transactions
        for t in c_txns:
            assert cust.created_at <= t.created_at, "Transaction cannot be earlier than customer creation"


def test_failure_reason_rules_and_recovery_cases():
    """Verify failure_reason is populated only on failed/abandoned transactions, and RecoveryCases match."""
    customers, transactions, recovery_cases = generate_seed_data(
        num_loyal=5,
        num_new=5,
        num_high_val=5,
        num_problematic=5,
        num_standard=5,
        recovery_case_sample_rate=0.5,
    )

    valid_reasons = {
        "bank_decline",
        "insufficient_funds",
        "bank_timeout",
        "network_error",
        "authentication_failed",
        "payment_method_expired",
        "unknown",
    }

    txn_by_id = {t.transaction_id: t for t in transactions}

    for t in transactions:
        if t.status in ["failed", "abandoned"]:
            assert t.failure_reason in valid_reasons
        else:
            assert t.failure_reason is None, f"Success/Pending transaction {t.transaction_id} should not have failure_reason"

    for rc in recovery_cases:
        assert rc.transaction_id in txn_by_id
        parent_txn = txn_by_id[rc.transaction_id]
        assert rc.amount_at_risk == parent_txn.amount
        assert parent_txn.status in ["failed", "abandoned"]
        assert rc.risk_score is None
        assert rc.recovery_probability is None
        assert rc.recommended_action is None
        assert rc.status == "pending"
        assert rc.attempt_count == 0
        assert rc.amount_recovered == 0.0


def test_full_seed_and_db_persistence():
    """Run full seed script and verify records persist in database."""
    seed_database()

    session = SessionLocal()
    try:
        customer_count = session.query(Customer).count()
        transaction_count = session.query(Transaction).count()
        recovery_case_count = session.query(RecoveryCase).count()

        assert customer_count == 1000
        assert transaction_count > 4800
        assert recovery_case_count > 300

        # Verify a sample customer with relationships
        sample_customer = session.query(Customer).first()
        assert sample_customer is not None
        assert len(sample_customer.transactions) > 0
    finally:
        session.close()
