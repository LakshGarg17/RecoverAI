"""
Webhooks Route Proxy (Day 7)
"""
from backend.app.api.v1.endpoints.webhooks import (
    router,
    razorpay_webhook_endpoint,
)

__all__ = ["router", "razorpay_webhook_endpoint"]
