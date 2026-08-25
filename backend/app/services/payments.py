import logging
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
                    "version": settings.VERSION
                })
            except Exception as e:
                logger.error(f"Failed to initialize Razorpay client: {e}")
                raise e
        return self._client

    def is_configured(self) -> bool:
        """Check if non-placeholder Razorpay keys are configured."""
        return (
            bool(self.key_id)
            and bool(self.key_secret)
            and not self.key_id.startswith("rzp_test_placeholder")
        )

    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a payment order.
        Amount is in subunit (paise for INR). Example: Rs. 500 = 50000 paise.
        """
        if not self.is_configured():
            logger.info("Razorpay in mock/placeholder mode. Returning simulated order.")
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
                "created_at": 1700000000,
            }

        payload = {
            "amount": amount,
            "currency": currency,
            "receipt": receipt or "rcpt_rec_default",
            "notes": notes or {},
            "payment_capture": 1,
        }
        return self.client.order.create(data=payload)

    def verify_payment_signature(
        self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str
    ) -> bool:
        """Verify Razorpay payment signature."""
        if not self.is_configured():
            return True
        try:
            self.client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            return False


payments_service = RazorpayService()
