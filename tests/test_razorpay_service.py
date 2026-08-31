"""
Unit Tests for Razorpay Service & Currency Utilities (Day 7)
Tests currency conversion precision, Razorpay Payment Links API invocation, error handling, and webhook signatures.
"""

import os
import sys
import hmac
import hashlib
import pytest
from unittest.mock import MagicMock, patch

# Ensure root & backend paths are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(root_dir, "backend")
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.utils.currency import rupees_to_paise, paise_to_rupees
from backend.services.razorpay_service import RazorpayService, razorpay_service, RazorpayServiceError
import razorpay


# ============================================================================
# 1. Currency Conversion Precision Tests
# ============================================================================

def test_currency_conversion_exact_values():
    """Verify standard INR rupee to integer paise conversion."""
    assert rupees_to_paise(100) == 10000
    assert rupees_to_paise(999.50) == 99950
    assert rupees_to_paise(14999) == 1499900
    assert rupees_to_paise(0.01) == 1
    assert rupees_to_paise(0) == 0


def test_currency_reverse_conversion():
    """Verify paise to INR rupee conversion."""
    assert paise_to_rupees(10000) == 100.0
    assert paise_to_rupees(99950) == 999.50
    assert paise_to_rupees(1499900) == 14999.0
    assert paise_to_rupees(1) == 0.01


def test_currency_invalid_amounts():
    """Verify negative and None values raise ValueError."""
    with pytest.raises(ValueError):
        rupees_to_paise(-50.0)

    with pytest.raises(ValueError):
        rupees_to_paise(None)

    with pytest.raises(ValueError):
        paise_to_rupees(-100)


# ============================================================================
# 2. Razorpay Service Payment Link Creation Tests
# ============================================================================

def test_payment_link_creation_mocked():
    """Verify that create_payment_link forms correct payload and extracts payment_link_id & url."""
    mock_client = MagicMock()
    mock_client.payment_link._is_mocked = True
    mock_client.payment_link.create.return_value = {
        "id": "plink_test1234567890",
        "short_url": "https://rzp.io/i/test1234",
        "status": "created",
        "amount": 1499900,
        "currency": "INR",
    }

    service = RazorpayService()
    service._client = mock_client

    result = service.create_payment_link(
        amount_paise=1499900,
        currency="INR",
        customer_info={"name": "Alice Tester", "email": "alice@example.com", "phone": "+919876543210"},
        description="Test Recovery Link",
        reference_id="ref_test_001",
    )

    assert result["success"] is True
    assert result["payment_link_id"] == "plink_test1234567890"
    assert result["payment_url"] == "https://rzp.io/i/test1234"
    assert result["amount_paise"] == 1499900

    mock_client.payment_link.create.assert_called_once()
    call_args = mock_client.payment_link.create.call_args[0][0]
    assert call_args["amount"] == 1499900
    assert call_args["currency"] == "INR"
    assert call_args["description"] == "Test Recovery Link"
    assert call_args["customer"]["email"] == "alice@example.com"


def test_payment_link_api_failure_handled():
    """Verify that simulated Razorpay API errors are caught and surfaced as failure dictionaries."""
    mock_client = MagicMock()
    mock_client.payment_link._is_mocked = True
    mock_client.payment_link.create.side_effect = razorpay.errors.BadRequestError("Amount is below minimum limit")

    service = RazorpayService()
    service._client = mock_client

    result = service.create_payment_link(
        amount_paise=50,  # below limit
        currency="INR",
    )

    assert result["success"] is False
    assert result["error_code"] == "BAD_REQUEST_ERROR"
    assert "minimum limit" in result["error_message"].lower()
    assert result["payment_link_id"] is None
    assert result["payment_url"] is None


def test_payment_link_test_mode_simulation():
    """Verify that service generates valid simulated links when running with placeholder keys in dev."""
    service = RazorpayService()
    service.key_id = "rzp_test_placeholder_key_id"
    service.key_secret = "placeholder_secret_key_here"

    result = service.create_payment_link(
        amount_paise=10000,
        currency="INR",
        description="Simulated Test Recovery Link",
    )

    assert result["success"] is True
    assert result["payment_link_id"].startswith("plink_")
    assert "rzp.io" in result["payment_url"]
    assert result["amount_paise"] == 10000


# ============================================================================
# 3. Webhook Signature Verification Tests
# ============================================================================

def test_webhook_signature_verification_valid():
    """Verify valid HMAC SHA256 webhook signature is accepted."""
    secret = "my_test_webhook_secret_123"
    body = '{"event": "payment_link.paid", "payload": {"payment": {"entity": {"id": "pay_test123"}}}}'
    valid_signature = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    service = RazorpayService()
    assert service.verify_webhook_signature(body, valid_signature, secret=secret) is True


def test_webhook_signature_verification_invalid():
    """Verify tampered or invalid signature is rejected."""
    secret = "my_test_webhook_secret_123"
    body = '{"event": "payment_link.paid"}'
    invalid_signature = "invalid_signature_hash_xyz"

    service = RazorpayService()
    assert service.verify_webhook_signature(body, invalid_signature, secret=secret) is False
    assert service.verify_webhook_signature(body, None, secret=secret) is False
