"""
Unit and Integration Tests for Recovery Execution Engine (Day 7)
Tests pre-execution validation, Razorpay dispatch, idempotency, rejection handling, and end-to-end recovery pipeline.
"""

import os
import sys
import uuid
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# Ensure root & backend paths are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ai.schemas import RecoveryAction, GuardrailStatus, ExecutionState
from backend.services.execution_engine import ExecutionEngine, ExecutionResult
from backend.services.razorpay_service import RazorpayService
from database.database import SessionLocal, init_db
from database.decision_models import save_recovery_decision
from database.execution_models import RecoveryExecution, get_execution_by_idempotency_key
from backend.app.main import app

client = TestClient(app)


def make_approved_decision(unique_suffix: str) -> dict:
    return {
        "decision_id": f"dec_exec_{unique_suffix}",
        "event_id": f"evt_exec_{unique_suffix}",
        "customer_id": f"cust_exec_{unique_suffix}",
        "selected_action": "PAYMENT_LINK",
        "decision_score": 90.0,
        "risk_score": 92.0,
        "estimated_recovery_probability": 0.85,
        "expected_recovery_value": 12750.0,
        "cart_value": 15000.0,
        "purchase_status": "abandoned",
        "purchase_intent_score": 85.0,
        "previous_purchases": 2,
    }


def make_blocked_decision(unique_suffix: str) -> dict:
    return {
        "decision_id": f"dec_block_{unique_suffix}",
        "event_id": f"evt_block_{unique_suffix}",
        "customer_id": f"cust_block_{unique_suffix}",
        "selected_action": "PAYMENT_LINK",
        "decision_score": 40.0,
        "risk_score": 35.0,  # Below threshold 60
        "estimated_recovery_probability": 0.30,
        "expected_recovery_value": 300.0,
        "cart_value": 1000.0,
        "purchase_status": "abandoned",
        "purchase_intent_score": 25.0,
    }


# ============================================================================
# 1. Execution Engine Core Tests
# ============================================================================

@pytest.mark.asyncio
async def test_approved_decision_executes_successfully():
    """
    Scenario: Valid approved decision with PAYMENT_LINK.
    Expectation: Status CREATED, payment_link_id generated, state READY_FOR_EXECUTION.
    """
    init_db()
    db = SessionLocal()
    try:
        dec = make_approved_decision(uuid.uuid4().hex[:8])
        save_recovery_decision(db, dec)

        engine = ExecutionEngine()
        result = await engine.execute_decision(
            decision_id=dec["decision_id"],
            db=db,
        )

        assert result.status == "CREATED"
        assert result.action == "PAYMENT_LINK"
        assert result.payment_link_id is not None
        assert result.payment_link_id.startswith("plink_")
        assert result.payment_url is not None
        assert "rzp.io" in result.payment_url

    finally:
        db.close()


@pytest.mark.asyncio
async def test_blocked_decision_cannot_execute():
    """
    Scenario: Decision has risk score 35.0 (blocked by guardrails).
    Expectation: Status REJECTED, reason specifies guardrail failure, no payment link created.
    """
    init_db()
    db = SessionLocal()
    try:
        dec = make_blocked_decision(uuid.uuid4().hex[:8])
        save_recovery_decision(db, dec)

        engine = ExecutionEngine()
        result = await engine.execute_decision(
            decision_id=dec["decision_id"],
            db=db,
        )

        assert result.status == "REJECTED"
        assert result.payment_link_id is None
        assert "not approved for execution" in result.reason.lower()

    finally:
        db.close()


@pytest.mark.asyncio
async def test_pre_execution_recheck_catches_stale_completion():
    """
    Scenario: Decision was previously approved, but real-time purchase status is now 'completed'.
    Expectation: Pre-execution re-check catches live state -> REJECTED.
    """
    init_db()
    db = SessionLocal()
    try:
        dec = make_approved_decision(uuid.uuid4().hex[:8])
        save_recovery_decision(db, dec)

        engine = ExecutionEngine()
        result = await engine.execute_decision(
            decision_id=dec["decision_id"],
            current_purchase_status="completed",
            db=db,
        )

        assert result.status == "REJECTED"
        assert "already completed" in result.reason.lower()

    finally:
        db.close()


@pytest.mark.asyncio
async def test_already_recovered_case_is_rejected():
    """
    Scenario: Event was already recovered previously.
    Expectation: Status REJECTED, reason indicates already completed/recovered.
    """
    init_db()
    db = SessionLocal()
    try:
        dec = make_approved_decision(uuid.uuid4().hex[:8])
        save_recovery_decision(db, dec)

        engine = ExecutionEngine()
        result = await engine.execute_decision(
            decision_id=dec["decision_id"],
            current_purchase_status="completed",
            db=db,
        )

        assert result.status == "REJECTED"
        assert result.payment_link_id is None

    finally:
        db.close()



@pytest.mark.asyncio
async def test_idempotency_prevents_duplicate_payment_links():
    """
    Scenario: Multiple rapid execution calls for the same decision.
    Expectation: Returns the existing execution record instead of creating a second Razorpay link.
    """
    init_db()
    db = SessionLocal()
    try:
        dec = make_approved_decision(uuid.uuid4().hex[:8])
        save_recovery_decision(db, dec)
        engine = ExecutionEngine()
        idemp_key = f"idemp_{uuid.uuid4().hex[:8]}"

        # First execution
        res1 = await engine.execute_decision(
            decision_id=dec["decision_id"],
            idempotency_key=idemp_key,
            db=db,
        )

        # Second execution
        res2 = await engine.execute_decision(
            decision_id=dec["decision_id"],
            idempotency_key=idemp_key,
            db=db,
        )

        assert res1.execution_id == res2.execution_id
        assert res1.payment_link_id == res2.payment_link_id
        assert res1.status == res2.status

    finally:
        db.close()


@pytest.mark.asyncio
async def test_non_payment_action_execution_internal():
    """
    Scenario: Action is PERSONALIZED_REMINDER.
    Expectation: Status CREATED, provider 'internal', payment_link_id None (no Razorpay call).
    """
    init_db()
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        reminder_decision = {
            "decision_id": f"dec_exec_rem_{suffix}",
            "event_id": f"evt_exec_rem_{suffix}",
            "customer_id": f"cust_exec_{suffix}",
            "selected_action": "PERSONALIZED_REMINDER",
            "decision_score": 85.0,
            "risk_score": 78.0,
            "estimated_recovery_probability": 0.78,
            "expected_recovery_value": 3900.0,
            "cart_value": 5000.0,
            "purchase_status": "abandoned",
            "purchase_intent_score": 75.0,
            "previous_purchases": 2,
        }
        save_recovery_decision(db, reminder_decision)

        engine = ExecutionEngine()
        result = await engine.execute_decision(
            decision_id=reminder_decision["decision_id"],
            db=db,
        )

        assert result.status == "CREATED"
        assert result.action == "PERSONALIZED_REMINDER"
        assert result.provider == "internal"
        assert result.payment_link_id is None

    finally:
        db.close()


# ============================================================================
# 2. API Endpoint Integration Tests
# ============================================================================

def test_api_execution_run_endpoint_approved():
    """Verify POST /api/execution/run returns 200 with payment_link details for approved decision."""
    init_db()
    db = SessionLocal()
    dec = make_approved_decision(uuid.uuid4().hex[:8])
    try:
        save_recovery_decision(db, dec)
    finally:
        db.close()

    payload = {"decision_id": dec["decision_id"]}
    response = client.post("/api/execution/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "CREATED"
    assert data["payment_link_id"] is not None
    assert data["payment_url"] is not None


def test_api_execution_run_endpoint_rejected_directly():
    """Verify POST /api/execution/run rejects invalid/blocked cases even when called directly."""
    payload = {
        "event_data": {
            "event_id": f"evt_direct_{uuid.uuid4().hex[:6]}",
            "customer_id": "cust_direct_reject",
            "cart_value": 50.0,  # below EV threshold
            "risk_score": 25.0,  # below risk threshold
            "purchase_status": "abandoned",
        }
    }
    response = client.post("/api/execution/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "REJECTED"
    assert "not approved" in data["reason"].lower()


def test_api_recovery_run_pipeline_approved():
    """Verify POST /api/recovery/run executes complete pipeline and creates payment link for VIP buyer."""
    unique_sfx = uuid.uuid4().hex[:6]
    payload = {
        "event_data": {
            "event_id": f"evt_e2e_vip_{unique_sfx}",
            "customer_id": f"cust_e2e_vip_{unique_sfx}",
            "cart_value": 18500.0,
            "currency": "INR",
            "payment_method": "UPI",
            "session_duration": 1200,
            "pages_viewed": 8,
            "purchase_status": "abandoned",
            "purchase_history": 3,
            "customer_lifetime_value": 45000.0,
            "risk_score": 90.0,
            "purchase_intent_score": 85.0,
        }
    }


    response = client.post("/api/recovery/run", json=payload)
    if response.status_code != 200:
        print("DEBUG RECOVERY RUN FAILED:", response.status_code, response.text)
    assert response.status_code == 200
    data = response.json()
    print("DEBUG DATA:", data)

    assert data["guardrail_status"] == "APPROVED"

    assert data["execution_status"] == "CREATED"
    assert data["expected_recovery_value"] > 1000.0
