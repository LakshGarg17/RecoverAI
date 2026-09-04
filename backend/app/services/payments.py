import logging
import time
from typing import Dict, Any, Optional

import razorpay
from app.core.config import settings

logger = logging.getLogger(__name__)


class RazorpayService:
    """Service wrapper for Razorpay Payment Gateway integration in Test Mode."""

    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self._client: Optional[razorpay.Client] = None

    @property
    def client(self) -> razorpay.Client:
        if self._client is None:
            try:
                self._client = razorpay.Client(
                    auth=(self.key_id, self.key_secret)
                )
                self._client.set_app_details({
                    "title": "RecoverAI",
                    "version": settings.VERSION,
                })
            except Exception as e:
                logger.error(f"Failed to initialize Razorpay client: {e}")
                raise
        return self._client

    def is_configured(self) -> bool:
        """Return True only when a real Razorpay TEST key is configured."""
        return (
            bool(self.key_id)
            and bool(self.key_secret)
            and self.key_id.startswith("rzp_test_")
            and not self.key_id.startswith("rzp_test_placeholder")
        )

    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a Razorpay order. Amount is in currency subunits."""
        if not self.is_configured():
            logger.info(
                "Razorpay is not configured with a valid TEST key. "
                "Returning simulated order."
            )
            return {
                "id": f"order_mock_{receipt or '101'}",
                "entity": "order",
                "amount": amount,
                "amount_paid": 0,
                "amount_due": amount,
                "currency": currency,
                "receipt": receipt,
                "status": "created",
                "attempts": 0,
                "notes": notes or {},
                "created_at": int(time.time()),
            }

        payload = {
            "amount": int(amount),
            "currency": currency,
            "receipt": receipt or "rcpt_rec_default",
            "notes": notes or {},
            "payment_capture": 1,
        }
        return self.client.order.create(data=payload)

    def create_payment_link(
        self,
        amount_paise: int,
        currency: str = "INR",
        customer_info: Optional[Dict[str, Any]] = None,
        description: str = "RecoverAI payment recovery",
        reference_id: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a Razorpay Standard Payment Link in TEST Mode."""
        amount_paise = int(amount_paise)

        if amount_paise < 100:
            return {
                "success": False,
                "error_code": "INVALID_AMOUNT",
                "error_message": "Payment Link amount must be at least ₹1.00.",
            }

        if not self.is_configured():
            logger.warning(
                "Payment Link creation blocked: a valid rzp_test_ key is required."
            )
            return {
                "success": False,
                "error_code": "RAZORPAY_TEST_MODE_NOT_CONFIGURED",
                "error_message": (
                    "RecoverAI requires a valid Razorpay Test Mode key "
                    "(rzp_test_...) to create a real Payment Link."
                ),
            }

        customer_info = customer_info or {}
        safe_reference_id = (reference_id or f"recoverai_{int(time.time())}")[:40]

        customer: Dict[str, Any] = {}
        if customer_info.get("name"):
            customer["name"] = str(customer_info["name"])[:100]
        if customer_info.get("email"):
            customer["email"] = str(customer_info["email"])[:100]
        if customer_info.get("phone") or customer_info.get("contact"):
            customer["contact"] = str(
                customer_info.get("phone") or customer_info.get("contact")
            )[:20]

        payload: Dict[str, Any] = {
            "amount": amount_paise,
            "currency": currency,
            "accept_partial": False,
            "description": description[:2048],
            "reference_id": safe_reference_id,
            "reminder_enable": False,
            "notify": {
                "sms": False,
                "email": False,
            },
            "notes": {
                str(k)[:50]: str(v)[:256]
                for k, v in (notes or {}).items()
            },
        }

        if customer:
            payload["customer"] = customer

        try:
            response = self.client.payment_link.create(data=payload)

            payment_link_id = response.get("id")
            payment_url = response.get("short_url")

            if not payment_link_id or not payment_url:
                logger.error(
                    "Razorpay Payment Link response missing id/short_url: %s",
                    response,
                )
                return {
                    "success": False,
                    "error_code": "INVALID_RAZORPAY_RESPONSE",
                    "error_message": (
                        "Razorpay did not return a Payment Link ID and URL."
                    ),
                }

            logger.info(
                "Created Razorpay TEST Payment Link %s for %s %s",
                payment_link_id,
                currency,
                amount_paise,
            )

            return {
                "success": True,
                "payment_link_id": payment_link_id,
                "payment_url": payment_url,
                "status": response.get("status", "created"),
                "amount": response.get("amount", amount_paise),
                "currency": response.get("currency", currency),
                "reference_id": response.get(
                    "reference_id", safe_reference_id
                ),
                "raw_response": response,
            }

        except Exception as exc:
            logger.exception("Razorpay Payment Link creation failed.")
            return {
                "success": False,
                "error_code": "RAZORPAY_PAYMENT_LINK_ERROR",
                "error_message": str(exc),
            }

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify Razorpay payment signature."""
        if not self.is_configured():
            return False

        try:
            self.client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            return False


razorpay_service = RazorpayService()
