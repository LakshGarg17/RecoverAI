"""
Razorpay Payment Service

Handles all Razorpay interactions for RecoverAI.

IMPORTANT:
- Only Razorpay Test Mode keys are accepted.
- AI/decision logic must never call Razorpay directly.
- All payment operations go through this service.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import razorpay

from app.core.config import settings


class RazorpayService:
    """
    Centralized Razorpay service for RecoverAI.

    This service is the only layer that should communicate
    directly with Razorpay APIs.
    """

    def __init__(self) -> None:
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.currency = settings.RAZORPAY_CURRENCY

        self._client: Optional[razorpay.Client] = None

    # ------------------------------------------------------------------
    # Razorpay client
    # ------------------------------------------------------------------

    @property
    def client(self) -> razorpay.Client:
        """
        Lazily create the Razorpay client.
        """
        if self._client is None:
            if not self.is_configured():
                raise RuntimeError(
                    "Razorpay is not configured with a valid Test Mode key."
                )

            self._client = razorpay.Client(
                auth=(self.key_id, self.key_secret)
            )

        return self._client

    # ------------------------------------------------------------------
    # Configuration / safety
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """
        Return True only when valid Razorpay TEST MODE credentials
        are configured.

        RecoverAI intentionally rejects live Razorpay keys.
        """

        if not self.key_id or not self.key_secret:
            return False

        if not isinstance(self.key_id, str):
            return False

        if not isinstance(self.key_secret, str):
            return False

        # Reject placeholder values.
        placeholder_values = {
            "",
            "rzp_test_placeholder_key_id",
            "placeholder_secret_key_here",
            "your_key_id",
            "your_key_secret",
            "test_key_id",
            "test_key_secret",
        }

        if self.key_id in placeholder_values:
            return False

        if self.key_secret in placeholder_values:
            return False

        # RecoverAI must NEVER use live Razorpay credentials.
        if not self.key_id.startswith("rzp_test_"):
            return False

        return True

    def get_mode(self) -> str:
        """
        Return the current Razorpay operating mode.
        """
        if self.key_id and self.key_id.startswith("rzp_test_"):
            return "test"

        return "unconfigured"

    # ------------------------------------------------------------------
    # Payment Orders
    # ------------------------------------------------------------------

    def create_order(
        self,
        amount_paise: int,
        currency: Optional[str] = None,
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Razorpay Test Mode order.

        Parameters
        ----------
        amount_paise:
            Amount in smallest currency unit.
            For INR, ₹100 = 10000 paise.

        currency:
            Currency code. Defaults to INR.

        receipt:
            Merchant-side receipt/reference identifier.

        notes:
            Additional metadata.
        """

        if not self.is_configured():
            return {
                "success": False,
                "error": "Razorpay Test Mode is not configured.",
                "mode": self.get_mode(),
            }

        if amount_paise <= 0:
            return {
                "success": False,
                "error": "Payment amount must be greater than zero.",
            }

        payload: Dict[str, Any] = {
            "amount": int(amount_paise),
            "currency": currency or self.currency,
        }

        if receipt:
            payload["receipt"] = str(receipt)[:40]

        if notes:
            payload["notes"] = notes

        try:
            response = self.client.order.create(data=payload)

            return {
                "success": True,
                "order_id": response.get("id"),
                "amount": response.get("amount"),
                "currency": response.get("currency"),
                "status": response.get("status"),
                "mode": "test",
                "raw": response,
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "mode": "test",
            }

    # ------------------------------------------------------------------
    # Payment Links
    # ------------------------------------------------------------------

    def create_payment_link(
        self,
        amount_paise: int,
        currency: Optional[str] = None,
        customer_info: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        reference_id: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Razorpay Payment Link in TEST MODE.

        This is the main execution mechanism used by RecoverAI
        when the Decision Engine selects PAYMENT_LINK.

        Razorpay expects the amount in paise for INR.

        Returns
        -------
        dict
            Structured result containing:

            success
            payment_link_id
            payment_url
            amount
            currency
            status
            mode
            raw
        """

        # --------------------------------------------------------------
        # Safety check 1: Test Mode only
        # --------------------------------------------------------------

        if not self.is_configured():
            return {
                "success": False,
                "error": (
                    "Razorpay Test Mode is not configured. "
                    "Live Razorpay credentials are not permitted."
                ),
                "mode": self.get_mode(),
            }

        # --------------------------------------------------------------
        # Safety check 2: amount validation
        # --------------------------------------------------------------

        if amount_paise <= 0:
            return {
                "success": False,
                "error": "Payment amount must be greater than zero.",
                "mode": "test",
            }

        # Razorpay Payment Links for INR require at least ₹1.
        if (currency or self.currency).upper() == "INR":
            if amount_paise < 100:
                return {
                    "success": False,
                    "error": (
                        "Razorpay Payment Link amount must be at least "
                        "₹1 (100 paise)."
                    ),
                    "mode": "test",
                }

        # --------------------------------------------------------------
        # Build customer information
        # --------------------------------------------------------------

        customer_info = customer_info or {}

        customer: Dict[str, Any] = {}

        name = customer_info.get("name")
        email = customer_info.get("email")
        contact = customer_info.get("contact")

        if name:
            customer["name"] = str(name)

        if email:
            customer["email"] = str(email)

        if contact:
            customer["contact"] = str(contact)

        # --------------------------------------------------------------
        # Build Payment Link payload
        # --------------------------------------------------------------

        payload: Dict[str, Any] = {
            "amount": int(amount_paise),
            "currency": currency or self.currency,
            "accept_partial": False,

            # RecoverAI itself controls recovery communication.
            # Razorpay should not independently send customer messages.
            "notify": {
                "sms": False,
                "email": False,
            },

            # Do not enable automatic reminders.
            "reminder_enable": False,
        }

        if customer:
            payload["customer"] = customer

        if description:
            payload["description"] = str(description)[:255]

        if reference_id:
            # Razorpay reference_id has a length limitation.
            payload["reference_id"] = str(reference_id)[:40]

        if notes:
            payload["notes"] = notes

        # --------------------------------------------------------------
        # Execute Razorpay API call
        # --------------------------------------------------------------

        try:
            response = self.client.payment_link.create(
                data=payload
            )

            payment_link_id = response.get("id")
            payment_url = response.get("short_url")

            # ----------------------------------------------------------
            # Validate Razorpay response
            # ----------------------------------------------------------

            if not payment_link_id:
                return {
                    "success": False,
                    "error": "Razorpay did not return a payment link ID.",
                    "mode": "test",
                    "raw": response,
                }

            if not payment_url:
                return {
                    "success": False,
                    "error": "Razorpay did not return a payment URL.",
                    "payment_link_id": payment_link_id,
                    "mode": "test",
                    "raw": response,
                }

            return {
                "success": True,
                "payment_link_id": payment_link_id,
                "payment_url": payment_url,
                "amount": response.get("amount"),
                "currency": response.get("currency"),
                "status": response.get("status"),
                "reference_id": response.get("reference_id"),
                "mode": "test",
                "raw": response,
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "mode": "test",
            }

    # ------------------------------------------------------------------
    # Payment signature verification
    # ------------------------------------------------------------------

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """
        Verify a Razorpay payment signature.

        Used when processing successful payment callbacks/webhooks.
        """

        if not self.is_configured():
            return False

        if not order_id or not payment_id or not signature:
            return False

        try:
            self.client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": order_id,
                    "razorpay_payment_id": payment_id,
                    "razorpay_signature": signature,
                }
            )

            return True

        except Exception:
            return False

    # ------------------------------------------------------------------
    # Webhook signature verification
    # ------------------------------------------------------------------

    def verify_webhook_signature(
        self,
        body: str | bytes,
        signature: str,
    ) -> bool:
        """
        Verify Razorpay webhook HMAC-SHA256 signature.

        Razorpay sends the webhook signature in the
        X-Razorpay-Signature header.
        """

        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

        if not webhook_secret:
            return False

        if not signature:
            return False

        try:
            if isinstance(body, bytes):
                body = body.decode("utf-8")

            self.client.utility.verify_webhook_signature(
                body,
                signature,
                webhook_secret,
            )

            return True

        except Exception:
            return False


# ----------------------------------------------------------------------
# Singleton instances
# ----------------------------------------------------------------------

# Primary name used by the execution engine.
razorpay_service = RazorpayService()

# Backward-compatible alias used by app.services imports / health checks.
payments_service = razorpay_service