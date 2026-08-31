"""
Razorpay Service Layer (Day 7)
Isolates all Razorpay SDK interactions for Test Mode payment recovery execution and webhook signature verification.
"""

import os
import sys
import hmac
import hashlib
import logging
import uuid
from typing import Dict, Any, Optional, Union

# Ensure root & backend paths are on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import razorpay
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class RazorpayServiceError(Exception):
    """Custom exception representing Razorpay API or signature errors."""
    def __init__(self, message: str, error_code: Optional[str] = None, raw_error: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "RAZORPAY_API_ERROR"
        self.raw_error = raw_error


class RazorpayService:
    """
    Encapsulated Razorpay Client Service for autonomous recovery.
    Operates strictly in Razorpay Test Mode (`rzp_test_...`).
    """

    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        self.currency = getattr(settings, "RAZORPAY_CURRENCY", "INR")
        self._client: Optional[razorpay.Client] = None
        self._init_client()

    def _init_client(self):
        """Initializes the Razorpay SDK client."""
        try:
            if self.key_id and self.key_secret:
                self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
                self._client.set_app_details({"title": "RecoverAI", "version": "1.0.0"})
        except Exception as e:
            logger.warning(f"Could not initialize Razorpay client with configured keys: {e}")
            self._client = None

    @property
    def client(self) -> razorpay.Client:
        if self._client is None:
            self._init_client()
            if self._client is None:
                # Create a minimal client instance
                self._client = razorpay.Client(auth=(self.key_id or "rzp_test_dummy", self.key_secret or "dummy_secret"))
        return self._client

    def is_live_configured(self) -> bool:
        """Checks if a valid, non-placeholder Razorpay Test key is provided."""
        return (
            bool(self.key_id)
            and not self.key_id.startswith("rzp_test_placeholder")
            and bool(self.key_secret)
            and not self.key_secret.startswith("placeholder")
        )

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
        Creates a Razorpay Payment Link in Test Mode.
        Calls client.payment_link.create(...) and returns payment_link_id and payment_url.
        """
        if amount_paise <= 0:
            raise ValueError(f"Amount in paise must be strictly positive, got {amount_paise}")

        cust = customer_info or {}
        cust_payload = {
            "name": cust.get("name", "Customer"),
            "email": cust.get("email", "customer@example.com"),
            "contact": cust.get("contact", cust.get("phone", "+919999999999")),
        }

        link_payload = {
            "amount": int(amount_paise),
            "currency": currency,
            "accept_partial": False,
            "description": description,
            "customer": cust_payload,
            "notify": {"sms": True, "email": True},
            "reminder_enable": True,
            "notes": notes or {},
        }
        if reference_id:
            link_payload["reference_id"] = str(reference_id)
        if expire_by:
            link_payload["expire_by"] = int(expire_by)

        try:
            # Check if live keys are present or if client is mocked
            if self.is_live_configured() or hasattr(self.client.payment_link, "_is_mocked"):
                response = self.client.payment_link.create(link_payload)
                
                payment_link_id = response.get("id") or f"plink_{uuid.uuid4().hex[:14]}"
                payment_url = response.get("short_url") or response.get("url") or f"https://rzp.io/i/{payment_link_id[6:]}"
                
                return {
                    "success": True,
                    "payment_link_id": payment_link_id,
                    "payment_url": payment_url,
                    "status": response.get("status", "created"),
                    "amount_paise": response.get("amount", amount_paise),
                    "currency": response.get("currency", currency),
                    "raw_response": response,
                }
            else:
                # Deterministic Test Mode simulation for local dev with placeholder credentials
                logger.info(f"Generating Test Mode simulated payment link for {amount_paise} paise.")
                link_id_suffix = uuid.uuid4().hex[:12]
                simulated_id = f"plink_{link_id_suffix}"
                simulated_url = f"https://rzp.io/i/{link_id_suffix}"
                
                return {
                    "success": True,
                    "payment_link_id": simulated_id,
                    "payment_url": simulated_url,
                    "status": "created",
                    "amount_paise": amount_paise,
                    "currency": currency,
                    "raw_response": {
                        "id": simulated_id,
                        "short_url": simulated_url,
                        "status": "created",
                        "amount": amount_paise,
                        "currency": currency,
                        "test_mode": True,
                    },
                }

        except razorpay.errors.BadRequestError as bre:
            logger.error(f"Razorpay Bad Request Error: {bre}")
            return {
                "success": False,
                "error_code": "BAD_REQUEST_ERROR",
                "error_message": str(bre),
                "payment_link_id": None,
                "payment_url": None,
            }
        except razorpay.errors.GatewayError as ge:
            logger.error(f"Razorpay Gateway Error: {ge}")
            return {
                "success": False,
                "error_code": "GATEWAY_ERROR",
                "error_message": str(ge),
                "payment_link_id": None,
                "payment_url": None,
            }
        except Exception as e:
            logger.error(f"Razorpay unexpected exception: {e}")
            return {
                "success": False,
                "error_code": "UNEXPECTED_ERROR",
                "error_message": str(e),
                "payment_link_id": None,
                "payment_url": None,
            }

    def verify_webhook_signature(
        self,
        payload_body: Union[str, bytes],
        signature: Optional[str],
        secret: Optional[str] = None
    ) -> bool:
        """
        Verifies Razorpay Webhook Signature using HMAC SHA256.
        """
        if not signature:
            logger.warning("Missing Razorpay webhook signature header.")
            return False

        webhook_secret = secret or self.webhook_secret or settings.RAZORPAY_WEBHOOK_SECRET
        if not webhook_secret:
            logger.warning("No Razorpay webhook secret configured for verification.")
            return False

        try:
            body_str = payload_body.decode("utf-8") if isinstance(payload_body, bytes) else str(payload_body)
            
            # Use Razorpay utility if available
            try:
                self.client.utility.verify_webhook_signature(body_str, signature, webhook_secret)
                return True
            except razorpay.errors.SignatureVerificationError:
                return False
            except Exception:
                # Direct HMAC-SHA256 fallback verification
                expected_signature = hmac.new(
                    webhook_secret.encode("utf-8"),
                    body_str.encode("utf-8"),
                    hashlib.sha256
                ).hexdigest()
                return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.warning(f"Error during webhook signature verification: {e}")
            return False


# Global singleton instance
razorpay_service = RazorpayService()

__all__ = [
    "RazorpayServiceError",
    "RazorpayService",
    "razorpay_service",
]
