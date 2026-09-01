"""recovery_execution_and_guardrails

Revision ID: 0002_recovery_execution
Revises: 0001_initial_schema
Create Date: 2026-08-31 20:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_recovery_execution"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Customers Table
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("customer_lifetime_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("previous_purchases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cart_abandonment_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_sessions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("customer_id"),
    )
    op.create_index(op.f("ix_customers_customer_id"), "customers", ["customer_id"], unique=False)
    op.create_index(op.f("ix_customers_email"), "customers", ["email"], unique=False)

    # 2. Transactions Table
    op.create_table(
        "transactions",
        sa.Column("transaction_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="INR"),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("purchase_status", sa.String(length=50), nullable=False, server_default="abandoned"),
        sa.Column("session_duration", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_viewed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("transaction_id"),
    )
    op.create_index(op.f("ix_transactions_transaction_id"), "transactions", ["transaction_id"], unique=False)
    op.create_index(op.f("ix_transactions_customer_id"), "transactions", ["customer_id"], unique=False)
    op.create_index(op.f("ix_transactions_purchase_status"), "transactions", ["purchase_status"], unique=False)

    # 3. AI Decisions Table (Day 4)
    op.create_table(
        "ai_decisions",
        sa.Column("decision_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("diagnosis", sa.String(length=64), nullable=False),
        sa.Column("recommended_action", sa.String(length=64), nullable=False),
        sa.Column("recovery_probability", sa.Float(), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("recommendation_confidence", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("reason_codes", sa.Text(), nullable=True),
        sa.Column("suggested_message", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("decision_id"),
    )
    op.create_index(op.f("ix_ai_decisions_decision_id"), "ai_decisions", ["decision_id"], unique=False)
    op.create_index(op.f("ix_ai_decisions_event_id"), "ai_decisions", ["event_id"], unique=False)
    op.create_index(op.f("ix_ai_decisions_customer_id"), "ai_decisions", ["customer_id"], unique=False)

    # 4. Recovery Decisions Table (Day 5)
    op.create_table(
        "recovery_decisions",
        sa.Column("decision_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("selected_action", sa.String(length=64), nullable=False),
        sa.Column("decision_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("expected_recovery_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("estimated_recovery_probability", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="MEDIUM"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("cart_value", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("purchase_status", sa.String(length=32), nullable=False, server_default="abandoned"),
        sa.Column("reasons", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("alternative_actions", sa.Text(), nullable=True),
        sa.Column("excluded_actions", sa.Text(), nullable=True),
        sa.Column("ai_recommended_action", sa.String(length=64), nullable=True),
        sa.Column("ai_recovery_probability", sa.Float(), nullable=True),
        sa.Column("ai_diagnosis_category", sa.String(length=64), nullable=True),
        sa.Column("divergence_reason", sa.Text(), nullable=True),
        sa.Column("policy_applied", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("decision_id"),
    )
    op.create_index(op.f("ix_recovery_decisions_decision_id"), "recovery_decisions", ["decision_id"], unique=False)
    op.create_index(op.f("ix_recovery_decisions_event_id"), "recovery_decisions", ["event_id"], unique=False)
    op.create_index(op.f("ix_recovery_decisions_customer_id"), "recovery_decisions", ["customer_id"], unique=False)

    # 5. Guardrail Audit Logs Table (Day 6)
    op.create_table(
        "guardrail_audit_logs",
        sa.Column("audit_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("decision_id", sa.String(length=64), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("requested_action", sa.String(length=64), nullable=False),
        sa.Column("final_action", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("execution_state", sa.String(length=32), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("recovery_probability", sa.Float(), nullable=True),
        sa.Column("expected_recovery_value", sa.Float(), nullable=True),
        sa.Column("cart_value", sa.Float(), nullable=True),
        sa.Column("policy_version", sa.String(length=32), nullable=False, server_default="v1.1"),
        sa.Column("checks_passed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checks_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checks_detail", sa.Text(), nullable=False),
        sa.Column("blocked_reasons", sa.Text(), nullable=True),
        sa.Column("reasons", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("audit_id"),
    )
    op.create_index(op.f("ix_guardrail_audit_logs_audit_id"), "guardrail_audit_logs", ["audit_id"], unique=False)
    op.create_index(op.f("ix_guardrail_audit_logs_decision_id"), "guardrail_audit_logs", ["decision_id"], unique=False)
    op.create_index(op.f("ix_guardrail_audit_logs_event_id"), "guardrail_audit_logs", ["event_id"], unique=False)
    op.create_index(op.f("ix_guardrail_audit_logs_customer_id"), "guardrail_audit_logs", ["customer_id"], unique=False)
    op.create_index(op.f("ix_guardrail_audit_logs_idempotency_key"), "guardrail_audit_logs", ["idempotency_key"], unique=False)

    # 6. Recovery Executions Table (Day 7)
    op.create_table(
        "recovery_executions",
        sa.Column("execution_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("decision_id", sa.String(length=64), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="CREATED"),
        sa.Column("execution_state", sa.String(length=32), nullable=False, server_default="READY_FOR_EXECUTION"),
        sa.Column("amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="INR"),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="razorpay"),
        sa.Column("provider_reference", sa.String(length=128), nullable=True),
        sa.Column("payment_link_id", sa.String(length=128), nullable=True),
        sa.Column("payment_url", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("execution_id"),
    )
    op.create_index(op.f("ix_recovery_executions_execution_id"), "recovery_executions", ["execution_id"], unique=False)
    op.create_index(op.f("ix_recovery_executions_decision_id"), "recovery_executions", ["decision_id"], unique=False)
    op.create_index(op.f("ix_recovery_executions_event_id"), "recovery_executions", ["event_id"], unique=False)
    op.create_index(op.f("ix_recovery_executions_customer_id"), "recovery_executions", ["customer_id"], unique=False)
    op.create_index(op.f("ix_recovery_executions_payment_link_id"), "recovery_executions", ["payment_link_id"], unique=False)
    op.create_index(op.f("ix_recovery_executions_idempotency_key"), "recovery_executions", ["idempotency_key"], unique=False)

    # 7. Recovery Records Table (Day 7)
    op.create_table(
        "recovery_records",
        sa.Column("recovery_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("execution_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="INITIATED"),
        sa.Column("original_amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("attempted_amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("recovered_amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("payment_id", sa.String(length=128), nullable=True),
        sa.Column("provider_reference", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("recovered_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("recovery_id"),
    )
    op.create_index(op.f("ix_recovery_records_recovery_id"), "recovery_records", ["recovery_id"], unique=False)
    op.create_index(op.f("ix_recovery_records_event_id"), "recovery_records", ["event_id"], unique=False)
    op.create_index(op.f("ix_recovery_records_customer_id"), "recovery_records", ["customer_id"], unique=False)
    op.create_index(op.f("ix_recovery_records_execution_id"), "recovery_records", ["execution_id"], unique=False)


def downgrade() -> None:
    op.drop_table("recovery_records")
    op.drop_table("recovery_executions")
    op.drop_table("guardrail_audit_logs")
    op.drop_table("recovery_decisions")
    op.drop_table("ai_decisions")
    op.drop_table("transactions")
    op.drop_table("customers")
