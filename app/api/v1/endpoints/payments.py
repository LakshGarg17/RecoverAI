from fastapi import APIRouter, HTTPException
from app.schemas.payment import PaymentOrderCreate, PaymentOrderResponse
from app.services.payments import payments_service

router = APIRouter()


@router.post("/orders", response_model=PaymentOrderResponse, summary="Create Recovery Payment Link/Order")
def create_payment_order(order_in: PaymentOrderCreate):
    """
    Create a Razorpay order in test mode for recovering an overdue invoice.
    """
    try:
        order = payments_service.create_order(
            amount=order_in.amount,
            currency=order_in.currency,
            receipt=order_in.receipt,
            notes=order_in.notes,
        )
        return order
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create payment order: {str(e)}")
