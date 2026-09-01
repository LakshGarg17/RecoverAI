"""
Unit and Integration Tests for Razorpay Webhook Ingestion Layer (Day 7)
Tests signature verification, payment success reconciliation, failure tracking, expiration handling, and audit trails.
"""

import os
import sys
import json
import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient

# Ensure root & backend paths are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app.core.config import settings
from database.database import SessionLocal, init_db
from database.execution_models import RecoveryExecution, save_execution_record
from database.recovery_models import RecoveryRecord, get_recovery_by_execution_id
from backend.app.main import app

client = TestClient(app)


def generate_test_signature(payload_str: str, secret: str = None) -> str:
    """Generates a valid HMAC SHA256 signature for test payloads."""
    sec = secret or settings.RAZORPAY_WEBHOOK_SECRET or "test_secret_123"
    return hmac.new(sec.encode("utf-8"), payload_str.encode("utf-8"), hashlib.sha256).hexdigest()


# Fixture for existing execution record awaiting payment
@pytest.fixture
def pending_execution_record() -> dict:
    return {
        "execution_id": "exec_webhook_test_001",
        "decision_id": "dec_webhook_test_001",
        "event_id": "evt_webhook_test_001",
        "customer_id": "cust_webhook_001",
        "action": "PAYMENT_LINK",
        "status": "CREATED",
        "execution_state": "READY_FOR_EXECUTION",
        "amount": 7500.0,
        "currency": "INR",
        "provider": "razorpay",
        "payment_link_id": "plink_webhook_test_12345",
        "payment_url": "https://rzp.io/i/webhook12345",
    }


# ============================================================================
# 1. Webhook Signature Security Tests
# ============================================================================

def test_webhook_missing_signature_rejected():
    """Verify webhook with missing signature header is rejected with 400."""
    payload = {"event": "payment_link.paid"}
    response = client.post("/api/webhooks/razorpay", json=payload)
    assert response.status_code == 400
    assert "signature" in response.json()["detail"].lower()


def test_webhook_invalid_signature_rejected():
    """Verify webhook with tampered / invalid signature is rejected with 400."""
    payload_str = json.dumps({"event": "payment_link.paid"})
    headers = {"X-Razorpay-Signature": "invalid_tampered_signature_123"}
    response = client.post(
        "/api/webhooks/razorpay",
        content=payload_str,
        headers=headers,
    )
    assert response.status_code == 400
    assert "invalid or missing webhook signature" in response.json()["detail"].lower()


# ============================================================================
# 2. Payment Success Reconciliation Tests
# ============================================================================

def test_webhook_payment_link_paid_reconciled(pending_execution_record):
    """
    Scenario: Valid payment_link.paid event received.
    Expectation:
      - Execution status updated to SUCCEEDED
      - RecoveryRecord created with recovered_amount, payment_id, status=RECOVERED
    """
    init_db()
    db = SessionLocal()
    try:
        # Seed execution record
        save_execution_record(db, pending_execution_record)

        payload_dict = {
            "event": "payment_link.paid",
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": pending_execution_record["payment_link_id"],
                        "amount_paid": 750000,  # 7500.00 INR
                        "status": "paid",
                    }
                },
                "payment": {
                    "entity": {
                        "id": "pay_test_succ_9999",
                        "amount": 750000,
                        "currency": "INR",
                        "status": "captured",
                        "method": "upi",
                    }
                }
            }
        }

        payload_str = json.dumps(payload_dict)
        sig = generate_test_signature(payload_str)

        response = client.post(
            "/api/webhooks/razorpay",
            content=payload_str,
            headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["result"] == "PAYMENT_RECOVERED"
        assert data["recovered_amount"] == 7500.0

        # Verify DB Execution Record
        updated_exec = db.query(RecoveryExecution).filter(
            RecoveryExecution.execution_id == pending_execution_record["execution_id"]
        ).first()
        assert updated_exec.status == "SUCCEEDED"

        # Verify DB Recovery Record
        recovery_rec = get_recovery_by_execution_id(db, pending_execution_record["execution_id"])
        assert recovery_rec is not None
        assert recovery_rec.status == "RECOVERED"
        assert recovery_rec.recovered_amount == 7500.0
        assert recovery_rec.payment_id == "pay_test_succ_9999"

    finally:
        db.close()


# ============================================================================
# 3. Payment Failure Tracking Tests
# ============================================================================

def test_webhook_payment_failed_tracked(pending_execution_record):
    """
    Scenario: Valid payment.failed event received.
    Expectation:
      - Execution status updated to FAILED
      - error_code and error_message populated
    """
    init_db()
    db = SessionLocal()
    try:
        save_execution_record(db, pending_execution_record)

        payload_dict = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_fail_8888",
                        "amount": 750000,
                        "error_code": "BAD_REQUEST_ERROR",
                        "error_description": "Payment was declined by customer bank due to insufficient funds.",
                        "notes": {
                            "decision_id": pending_execution_record["decision_id"],
                            "payment_link_id": pending_execution_record["payment_link_id"],
                        }
                    }
                }
            }
        }

        payload_str = json.dumps(payload_dict)
        sig = generate_test_signature(payload_str)

        response = client.post(
            "/api/webhooks/razorpay",
            content=payload_str,
            headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "PAYMENT_FAILED"

        # Verify DB Execution Record
        updated_exec = db.query(RecoveryExecution).filter(
            RecoveryExecution.execution_id == pending_execution_record["execution_id"]
        ).first()
        assert updated_exec.status == "FAILED"
        assert updated_exec.error_code == "BAD_REQUEST_ERROR"
        assert "insufficient funds" in updated_exec.error_message.lower()

    finally:
        db.close()


# ============================================================================
# 4. Payment Link Expiration & Unrecognized Event Tests
# ============================================================================

def test_webhook_payment_link_expired_handled(pending_execution_record):
    """
    Scenario: payment_link.expired event received.
    Expectation: Execution status updated to EXPIRED.
    """
    init_db()
    db = SessionLocal()
    try:
        save_execution_record(db, pending_execution_record)

        payload_dict = {
            "event": "payment_link.expired",
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": pending_execution_record["payment_link_id"],
                        "status": "expired",
                    }
                }
            }
        }

        payload_str = json.dumps(payload_dict)
        sig = generate_test_signature(payload_str)

        response = client.post(
            "/api/webhooks/razorpay",
            content=payload_str,
            headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "PAYMENT_LINK_EXPIRED"

        updated_exec = db.query(RecoveryExecution).filter(
            RecoveryExecution.execution_id == pending_execution_record["execution_id"]
        ).first()
        assert updated_exec.status == "EXPIRED"

    finally:
        db.close()


def test_webhook_unrecognized_event_ignored_gracefully():
    """
    Scenario: Webhook with unrecognized event type (e.g. invoice.paid).
    Expectation: Handled gracefully without error (200 OK, status: ignored).
    """
    payload_dict = {
        "event": "invoice.paid",
        "payload": {}
    }
    payload_str = json.dumps(payload_dict)
    sig = generate_test_signature(payload_str)

    response = client.post(
        "/api/webhooks/razorpay",
        content=payload_str,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"


def test_webhook_duplicate_event_handling_idempotent(pending_execution_record):
    """
    Scenario: Duplicate webhook arrival for the same payment success event.
    Expectation: Handled safely, remains SUCCEEDED without creating duplicated records or crashing.
    """
    init_db()
    db = SessionLocal()
    try:
        save_execution_record(db, pending_execution_record)

        payload_dict = {
            "event": "payment_link.paid",
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": pending_execution_record["payment_link_id"],
                        "amount_paid": 750000,
                        "status": "paid",
                    }
                },
                "payment": {
                    "entity": {
                        "id": "pay_test_dup_1234",
                        "amount": 750000,
                        "currency": "INR",
                        "status": "captured",
                    }
                }
            }
        }

        payload_str = json.dumps(payload_dict)
        sig = generate_test_signature(payload_str)

        # First webhook arrival
        r1 = client.post(
            "/api/webhooks/razorpay",
            content=payload_str,
            headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
        )
        assert r1.status_code == 200

        # Duplicate webhook arrival
        r2 = client.post(
            "/api/webhooks/razorpay",
            content=payload_str,
            headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
        )
        assert r2.status_code == 200

        # Verify state
        updated_exec = db.query(RecoveryExecution).filter(
            RecoveryExecution.execution_id == pending_execution_record["execution_id"]
        ).first()
        assert updated_exec.status == "SUCCEEDED"

    finally:
        db.close()

