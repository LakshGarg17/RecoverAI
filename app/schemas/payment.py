from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PaymentOrderCreate(BaseModel):
    amount: int = Field(..., description="Amount in subunit (e.g., paise for INR)", json_schema_extra={"example": 50000})
    currency: str = Field("INR", description="Currency code (e.g. INR, USD)", json_schema_extra={"example": "INR"})
    receipt: Optional[str] = Field(None, description="Receipt identifier", json_schema_extra={"example": "rcpt_rec_001"})
    notes: Optional[Dict[str, str]] = Field(default_factory=dict)


class PaymentOrderResponse(BaseModel):
    id: str = Field(..., json_schema_extra={"example": "order_dummy_12345"})
    entity: str = "order"
    amount: int = 50000
    amount_paid: int = 0
    amount_due: int = 50000
    currency: str = "INR"
    receipt: Optional[str] = None
    status: str = "created"
    attempts: int = 0
    notes: Optional[Dict[str, str]] = None
    created_at: int = 0
