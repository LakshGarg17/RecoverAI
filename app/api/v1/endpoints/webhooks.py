"""
Webhook Ingestion Endpoints (Day 7)
Processes and validates inbound Razorpay Webhooks (payment success, failure, expiration).
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from backend.services.razorpay_service import razorpay_service
from backend.utils.currency import paise_to_rupees
from database.execution_models import get_execution_by_payment_link_id, save_execution_record, RecoveryExecution
from database.recovery_models import save_recovery_record, get_recovery_by_execution_id
from database.audit_models import save_guardrail_audit_log

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/razorpay",
    status_code=status.HTTP_200_OK,
    summary="Inbound Razorpay Webhook Ingestion (Day 7)",
    description="Validates cryptographic signature and reconciles payment success, failure, or expiration."
)
async def razorpay_webhook_endpoint(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db)
):
    """
    Handles Razorpay Webhook Events:
    - Verifies HMAC SHA256 signature
    - Reconciles payment_link.paid / payment.captured -> SUCCEEDED + RecoveryRecord
    - Reconciles payment.failed -> FAILED + Failure details
    - Reconciles payment_link.expired -> EXPIRED
    - Persists audit logs for every state transition
    """
    raw_body = await request.body()

    # 1. Verify Webhook Signature
    # If signature verification is enabled and fails, reject
    if not razorpay_service.verify_webhook_signature(raw_body, x_razorpay_signature):
        logger.warning("Razorpay webhook signature verification failed.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing webhook signature."
        )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.error(f"Invalid JSON payload received in webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON body: {str(e)}"
        )

    event_type = payload.get("event", "unknown")
    event_payload = payload.get("payload", {})
    now_dt = datetime.utcnow()

    logger.info(f"Received verified Razorpay webhook: '{event_type}'")

    # Extract entities
    payment_link_entity = event_payload.get("payment_link", {}).get("entity", {})
    payment_entity = event_payload.get("payment", {}).get("entity", {})

    plink_id = (
        payment_link_entity.get("id")
        or payment_entity.get("notes", {}).get("payment_link_id")
        or payment_entity.get("payment_link_id")
    )
    decision_id = payment_entity.get("notes", {}).get("decision_id") or payment_link_entity.get("notes", {}).get("decision_id")
    event_id = payment_entity.get("notes", {}).get("event_id") or payment_link_entity.get("notes", {}).get("event_id")
    payment_id = payment_entity.get("id")

    # Locate matching execution record
    execution = None
    if plink_id:
        execution = get_execution_by_payment_link_id(db, plink_id)
    if execution is None and decision_id:
        execution = db.query(RecoveryExecution).filter(RecoveryExecution.decision_id == decision_id).first()

    # =========================================================================
    # Event Case 1: Payment Succeeded / Link Paid
    # =========================================================================
    if event_type in ("payment_link.paid", "payment.captured", "order.paid"):
        amount_paise = payment_entity.get("amount") or payment_link_entity.get("amount_paid") or payment_link_entity.get("amount") or 0
        recovered_rupees = paise_to_rupees(amount_paise)

        if execution:
            execution.status = "SUCCEEDED"
            execution.execution_state = "SUCCEEDED"
            execution.provider_reference = payment_id or execution.provider_reference
            execution.updated_at = now_dt
            db.commit()
            db.refresh(execution)

            # Create or update permanent RecoveryRecord
            rec_payload = {
                "recovery_id": f"rec_{execution.execution_id[5:]}" if len(execution.execution_id) > 5 else f"rec_{uuid.uuid4().hex[:12]}",
                "event_id": execution.event_id,
                "customer_id": execution.customer_id,
                "execution_id": execution.execution_id,
                "action": execution.action,
                "status": "RECOVERED",
                "original_amount": execution.amount,
                "attempted_amount": execution.amount,
                "recovered_amount": recovered_rupees if recovered_rupees > 0 else execution.amount,
                "payment_id": payment_id,
                "provider_reference": plink_id or payment_id,
                "recovered_at": now_dt,
            }
            save_recovery_record(db, rec_payload)

            # Audit event
            save_guardrail_audit_log(db, {
                "decision_id": execution.decision_id,
                "event_id": execution.event_id,
                "customer_id": execution.customer_id,
                "action": execution.action,
                "status": "APPROVED",
                "execution_state": "SUCCEEDED",
                "reason": f"Payment successfully captured via Razorpay ({payment_id}, ₹{recovered_rupees:,.2f}).",
                "idempotency_key": f"webhook:paid:{execution.execution_id}",
            })

            logger.info(f"Payment recovered for execution {execution.execution_id}: ₹{recovered_rupees:,.2f}")

        return {
            "status": "processed",
            "event": event_type,
            "result": "PAYMENT_RECOVERED",
            "payment_id": payment_id,
            "recovered_amount": recovered_rupees,
        }

    # =========================================================================
    # Event Case 2: Payment Failed
    # =========================================================================
    elif event_type in ("payment.failed", "payment_link.failed"):
        error_code = payment_entity.get("error_code") or "PAYMENT_DECLINED"
        error_desc = payment_entity.get("error_description") or "Customer payment attempt failed."

        if execution:
            execution.status = "FAILED"
            execution.execution_state = "FAILED"
            execution.error_code = error_code
            execution.error_message = error_desc
            execution.updated_at = now_dt
            db.commit()
            db.refresh(execution)

            # Audit event
            save_guardrail_audit_log(db, {
                "decision_id": execution.decision_id,
                "event_id": execution.event_id,
                "customer_id": execution.customer_id,
                "action": execution.action,
                "status": "FAILED",
                "execution_state": "FAILED",
                "reason": f"Payment attempt failed: {error_desc} (Code: {error_code})",
                "idempotency_key": f"webhook:failed:{execution.execution_id}",
            })

            logger.warning(f"Payment failed for execution {execution.execution_id}: {error_desc}")

        return {
            "status": "processed",
            "event": event_type,
            "result": "PAYMENT_FAILED",
            "error_code": error_code,
            "error_message": error_desc,
        }

    # =========================================================================
    # Event Case 3: Payment Link Expired / Cancelled
    # =========================================================================
    elif event_type in ("payment_link.expired", "payment_link.cancelled"):
        if execution:
            execution.status = "EXPIRED"
            execution.execution_state = "EXPIRED"
            execution.updated_at = now_dt
            db.commit()
            db.refresh(execution)

            # Audit event
            save_guardrail_audit_log(db, {
                "decision_id": execution.decision_id,
                "event_id": execution.event_id,
                "customer_id": execution.customer_id,
                "action": execution.action,
                "status": "EXPIRED",
                "execution_state": "EXPIRED",
                "reason": f"Payment link expired without completion.",
                "idempotency_key": f"webhook:expired:{execution.execution_id}",
            })

            logger.info(f"Payment link expired for execution {execution.execution_id}")

        return {
            "status": "processed",
            "event": event_type,
            "result": "PAYMENT_LINK_EXPIRED",
        }

    # =========================================================================
    # Event Case 4: Unrecognized / Other Event
    # =========================================================================
    else:
        logger.info(f"Unhandled Razorpay webhook event '{event_type}'. Ignored gracefully.")
        return {
            "status": "ignored",
            "event": event_type,
            "message": "Event acknowledged but no action required.",
        }
