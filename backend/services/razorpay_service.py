"""
RecoverAI Razorpay Service Layer

Centralized Razorpay integration for payment recovery.

IMPORTANT SECURITY RULES
------------------------
1. RecoverAI operates ONLY in Razorpay Test Mode.
2. Live Razorpay keys are rejected.
3. The AI/Decision Engine never calls Razorpay directly.
4. All Razorpay API calls pass through this service.
5. Payment links do not automatically send customer notifications.
6. Webhook signatures are verified using HMAC-SHA256.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import sys
import uuid
from typing import Any, Dict, Optional, Union

import razorpay

# ----------------------------------------------------------------------
# Ensure project root and backend are importable
# ----------------------------------------------------------------------

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))

for path in [PROJECT_ROOT, BACKEND_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from backend.app.core.config import settings


logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Custom exception
# ----------------------------------------------------------------------

class RazorpayServiceError(Exception):
    """Custom exception for Razorpay API/service errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        raw_error: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "RAZORPAY_API_ERROR"
        self.raw_error = raw_error


# ----------------------------------------------------------------------
# Razorpay Service
# ----------------------------------------------------------------------

class RazorpayService:
    """
    Centralized Razorpay service used by RecoverAI.

    This class is intentionally Test Mode only.
    """

    def __init__(self) -> None:
        self.key_id = getattr(settings, "RAZORPAY_KEY_ID", None)
        self.key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", None)
        self.webhook_secret = getattr(
            settings,
            "RAZORPAY_WEBHOOK_SECRET",
            None,
        )
        self.currency = getattr(
            settings,
            "RAZORPAY_CURRENCY",
            "INR",
        )

        self._client: Optional[razorpay.Client] = None

        self._init_client()

    # ------------------------------------------------------------------
    # Razorpay client
    # ------------------------------------------------------------------

    def _init_client(self) -> None:
        """Initialize Razorpay SDK client when valid credentials exist."""

        try:
            if not self.is_configured():
                logger.warning(
                    "Razorpay Test Mode credentials are not configured."
                )
                self._client = None
                return

            self._client = razorpay.Client(
                auth=(self.key_id, self.key_secret)
            )

            # Optional SDK application identification.
            try:
                self._client.set_app_details(
                    {
                        "title": "RecoverAI",
                        "version": "1.0.0",
                    }
                )
            except Exception:
                # set_app_details is not required for functionality.
                pass

        except Exception as exc:
            logger.warning(
                "Could not initialize Razorpay client: %s",
                exc,
            )
            self._client = None

    @property
    def client(self) -> razorpay.Client:
        """
        Return the Razorpay client.

        Unlike the previous implementation, this does NOT create
        a fake client when credentials are missing.
        """

        if self._client is None:
            self._init_client()

        if self._client is None:
            raise RazorpayServiceError(
                "Razorpay Test Mode is not configured."
            )

        return self._client

    # ------------------------------------------------------------------
    # Configuration / safety
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """
        Check whether valid Razorpay TEST MODE credentials are configured.

        RecoverAI explicitly rejects live keys.
        """

        if not self.key_id or not self.key_secret:
            return False

        if not isinstance(self.key_id, str):
            return False

        if not isinstance(self.key_secret, str):
            return False

        # Explicitly reject live Razorpay credentials.
        if not self.key_id.startswith("rzp_test_"):
            logger.error(
                "SECURITY: Razorpay key is not a Test Mode key. "
                "Live keys are not permitted."
            )
            return False

        # Reject obvious placeholder credentials.
        placeholder_key_values = {
            "",
            "rzp_test_placeholder_key_id",
            "your_key_id",
            "test_key_id",
        }

        placeholder_secret_values = {
            "",
            "placeholder_secret_key_here",
            "your_key_secret",
            "test_key_secret",
        }

        if self.key_id in placeholder_key_values:
            return False

        if self.key_secret in placeholder_secret_values:
            return False

        if self.key_secret.startswith("placeholder"):
            return False

        return True

    def is_live_configured(self) -> bool:
        """
        Backward-compatible method.

        Historical code uses this method name, but RecoverAI
        actually means "valid Test Mode credentials configured".

        Kept to avoid breaking existing imports/tests.
        """

        return self.is_configured()

    def get_mode(self) -> str:
        """Return the current Razorpay operating mode."""

        if self.key_id and self.key_id.startswith("rzp_test_"):
            if self.is_configured():
                return "test"

            return "test_unconfigured"

        return "unconfigured"

    # ------------------------------------------------------------------
    # Create Razorpay Order
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

        currency:
            Currency code. Defaults to configured currency.

        receipt:
            Merchant-side receipt/reference.

        notes:
            Additional metadata.
        """

        if not self.is_configured():
            return {
                "success": False,
                "error_code": "RAZORPAY_NOT_CONFIGURED",
                "error_message": (
                    "Razorpay Test Mode is not configured."
                ),
                "mode": self.get_mode(),
            }

        if amount_paise <= 0:
            return {
                "success": False,
                "error_code": "INVALID_AMOUNT",
                "error_message": (
                    f"Amount in paise must be positive, "
                    f"got {amount_paise}"
                ),
                "mode": "test",
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
            response = self.client.order.create(
                data=payload
            )

            return {
                "success": True,
                "order_id": response.get("id"),
                "amount": response.get(
                    "amount",
                    amount_paise,
                ),
                "amount_paise": response.get(
                    "amount",
                    amount_paise,
                ),
                "currency": response.get(
                    "currency",
                    currency or self.currency,
                ),
                "status": response.get(
                    "status",
                    "created",
                ),
                "mode": "test",
                "raw_response": response,
                "raw": response,
            }

        except razorpay.errors.BadRequestError as exc:
            logger.error(
                "Razorpay order BadRequestError: %s",
                exc,
            )

            return {
                "success": False,
                "error_code": "BAD_REQUEST_ERROR",
                "error_message": str(exc),
                "mode": "test",
            }

        except razorpay.errors.GatewayError as exc:
            logger.error(
                "Razorpay order GatewayError: %s",
                exc,
            )

            return {
                "success": False,
                "error_code": "GATEWAY_ERROR",
                "error_message": str(exc),
                "mode": "test",
            }

        except Exception as exc:
            logger.error(
                "Unexpected Razorpay order error: %s",
                exc,
            )

            return {
                "success": False,
                "error_code": "UNEXPECTED_ERROR",
                "error_message": str(exc),
                "mode": "test",
            }

    # ------------------------------------------------------------------
    # Create Payment Link
    # ------------------------------------------------------------------

    def create_payment_link(
        self,
        amount_paise: int,
        currency: str = "INR",
        customer_info: Optional[Dict[str, Any]] = None,
        description: str = "RecoverAI Payment Link",
        reference_id: Optional[str] = None,
        expire_by: Optional[int] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Razorpay Payment Link in TEST MODE.

        This method is called by the Execution Engine when
        PAYMENT_LINK is selected by the Decision Engine.

        No fake/simulated payment link is returned here.
        A successful response means Razorpay actually accepted
        the Payment Link creation request.
        """

        # --------------------------------------------------------------
        # Safety check: Razorpay Test Mode only
        # --------------------------------------------------------------

        if not self.is_configured():
            return {
                "success": False,
                "error_code": "RAZORPAY_NOT_CONFIGURED",
                "error_message": (
                    "Razorpay Test Mode is not configured. "
                    "Live Razorpay credentials are not permitted."
                ),
                "payment_link_id": None,
                "payment_url": None,
                "mode": self.get_mode(),
            }

        # --------------------------------------------------------------
        # Amount validation
        # --------------------------------------------------------------

        if amount_paise <= 0:
            return {
                "success": False,
                "error_code": "INVALID_AMOUNT",
                "error_message": (
                    f"Amount in paise must be strictly positive, "
                    f"got {amount_paise}"
                ),
                "payment_link_id": None,
                "payment_url": None,
                "mode": "test",
            }

        currency = (currency or self.currency).upper()

        # Razorpay INR minimum = ₹1 = 100 paise.
        if currency == "INR" and amount_paise < 100:
            return {
                "success": False,
                "error_code": "AMOUNT_TOO_LOW",
                "error_message": (
                    "Razorpay Payment Link amount must be at least "
                    "₹1 (100 paise)."
                ),
                "payment_link_id": None,
                "payment_url": None,
                "mode": "test",
            }

        # --------------------------------------------------------------
        # Customer information
        # --------------------------------------------------------------

        customer = customer_info or {}

        customer_payload: Dict[str, Any] = {}

        if customer.get("name"):
            customer_payload["name"] = str(
                customer["name"]
            )[:100]

        if customer.get("email"):
            customer_payload["email"] = str(
                customer["email"]
            )[:100]

        contact = customer.get(
            "contact",
            customer.get("phone"),
        )

        if contact:
            customer_payload["contact"] = str(
                contact
            )[:15]

        # --------------------------------------------------------------
        # Build Payment Link payload
        # --------------------------------------------------------------

        link_payload: Dict[str, Any] = {
            "amount": int(amount_paise),
            "currency": currency,
            "accept_partial": False,

            # RecoverAI owns customer recovery communication.
            # Razorpay should NOT send duplicate messages.
            "notify": {
                "sms": False,
                "email": False,
            },

            # RecoverAI controls follow-up timing.
            "reminder_enable": False,
        }

        if description:
            link_payload["description"] = str(
                description
            )[:255]

        if customer_payload:
            link_payload["customer"] = customer_payload

        if reference_id:
            link_payload["reference_id"] = str(
                reference_id
            )[:40]

        if expire_by:
            link_payload["expire_by"] = int(
                expire_by
            )

        if notes:
            link_payload["notes"] = notes

        # --------------------------------------------------------------
        # Call Razorpay
        # --------------------------------------------------------------

        try:
            response = self.client.payment_link.create(
                link_payload
            )

            payment_link_id = response.get("id")

            payment_url = (
                response.get("short_url")
                or response.get("url")
            )

            # ----------------------------------------------------------
            # Validate response
            # ----------------------------------------------------------

            if not payment_link_id:
                logger.error(
                    "Razorpay returned Payment Link response "
                    "without an ID."
                )

                return {
                    "success": False,
                    "error_code": "INVALID_RAZORPAY_RESPONSE",
                    "error_message": (
                        "Razorpay did not return a payment link ID."
                    ),
                    "payment_link_id": None,
                    "payment_url": payment_url,
                    "mode": "test",
                    "raw_response": response,
                }

            if not payment_url:
                logger.error(
                    "Razorpay Payment Link %s did not contain a URL.",
                    payment_link_id,
                )

                return {
                    "success": False,
                    "error_code": "MISSING_PAYMENT_URL",
                    "error_message": (
                        "Razorpay did not return a payment URL."
                    ),
                    "payment_link_id": payment_link_id,
                    "payment_url": None,
                    "mode": "test",
                    "raw_response": response,
                }

            logger.info(
                "Razorpay Test Mode Payment Link created: %s",
                payment_link_id,
            )

            return {
                "success": True,
                "payment_link_id": payment_link_id,
                "payment_url": payment_url,
                "status": response.get(
                    "status",
                    "created",
                ),
                "amount": response.get(
                    "amount",
                    amount_paise,
                ),
                "amount_paise": response.get(
                    "amount",
                    amount_paise,
                ),
                "currency": response.get(
                    "currency",
                    currency,
                ),
                "reference_id": response.get(
                    "reference_id",
                    reference_id,
                ),
                "mode": "test",
                "raw_response": response,
                "raw": response,
            }

        except razorpay.errors.BadRequestError as exc:
            logger.error(
                "Razorpay Payment Link BadRequestError: %s",
                exc,
            )

            return {
                "success": False,
                "error_code": "BAD_REQUEST_ERROR",
                "error_message": str(exc),
                "payment_link_id": None,
                "payment_url": None,
                "mode": "test",
            }

        except razorpay.errors.GatewayError as exc:
            logger.error(
                "Razorpay Payment Link GatewayError: %s",
                exc,
            )

            return {
                "success": False,
                "error_code": "GATEWAY_ERROR",
                "error_message": str(exc),
                "payment_link_id": None,
                "payment_url": None,
                "mode": "test",
            }

        except Exception as exc:
            logger.exception(
                "Unexpected Razorpay Payment Link error."
            )

            return {
                "success": False,
                "error_code": "UNEXPECTED_ERROR",
                "error_message": str(exc),
                "payment_link_id": None,
                "payment_url": None,
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
        Verify Razorpay payment signature.
        """

        if not self.is_configured():
            return False

        if not order_id:
            return False

        if not payment_id:
            return False

        if not signature:
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

        except razorpay.errors.SignatureVerificationError:
            logger.warning(
                "Razorpay payment signature verification failed."
            )
            return False

        except Exception as exc:
            logger.warning(
                "Payment signature verification error: %s",
                exc,
            )
            return False

    # ------------------------------------------------------------------
    # Webhook signature verification
    # ------------------------------------------------------------------

    def verify_webhook_signature(
        self,
        payload_body: Union[str, bytes],
        signature: Optional[str],
        secret: Optional[str] = None,
    ) -> bool:
        """
        Verify Razorpay webhook signature using HMAC-SHA256.

        Razorpay signs the raw request body with the webhook secret.
        """

        if not signature:
            logger.warning(
                "Missing Razorpay webhook signature."
            )
            return False

        webhook_secret = (
            secret
            or self.webhook_secret
            or getattr(
                settings,
                "RAZORPAY_WEBHOOK_SECRET",
                None,
            )
        )

        if not webhook_secret:
            logger.warning(
                "No Razorpay webhook secret configured."
            )
            return False

        try:
            if isinstance(payload_body, bytes):
                body_bytes = payload_body
            else:
                body_bytes = str(payload_body).encode(
                    "utf-8"
                )

            # ----------------------------------------------------------
            # Direct HMAC-SHA256 verification
            # ----------------------------------------------------------

            expected_signature = hmac.new(
                webhook_secret.encode("utf-8"),
                body_bytes,
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(
                expected_signature,
                signature,
            )

        except Exception as exc:
            logger.warning(
                "Webhook signature verification error: %s",
                exc,
            )
            return False


# ----------------------------------------------------------------------
# Global singleton
# ----------------------------------------------------------------------

razorpay_service = RazorpayService()

# IMPORTANT:
# app.services.payments imports this name.
# Keeping this alias prevents the Render startup ImportError.
payments_service = razorpay_service


# ----------------------------------------------------------------------
# Public exports
# ----------------------------------------------------------------------

__all__ = [
    "RazorpayServiceError",
    "RazorpayService",
    "razorpay_service",
    "payments_service",
]