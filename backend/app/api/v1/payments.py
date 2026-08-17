from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import EntityNotFoundError
from app.core.security import get_current_user_strict
from app.models.user import User
from app.schemas.order import (
    BlipPayInitiateResponse,
    BlipPaymentRecordResponse,
    BlipPayWebhookPayload,
    OrderCreateRequest,
    OrderResponse,
)
from app.schemas.payment import (
    InitiatePaymentRequest,
    PaymentIntentResponse,
    PaymentStatusResponse,
)
from app.services.order_service import OrderService
from app.services.payment_intent_service import PaymentIntentService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments (Blip Pay & Escrow)"])


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(db=db)


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(db=db)


@router.post(
    "/initiate",
    response_model=BlipPayInitiateResponse,
    status_code=201,
    summary="Initiate Blip Pay checkout intent",
    description="Locks inventory row, generates unique Blip Pay intent reference, provides duplicate payment protection, and creates initiated order.",
)
def initiate_checkout(
    body: OrderCreateRequest,
    service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user_strict),
):
    # Buyer is always the authenticated user.
    return service.initiate_checkout(
        buyer_id=current_user.id,
        listing_id=body.listing_id,
        amount=body.amount,
    )




def get_intent_service(db: Session = Depends(get_db)) -> PaymentIntentService:
    return PaymentIntentService(db=db)


@router.post(
    "/intent",
    response_model=PaymentIntentResponse,
    status_code=201,
    summary="Create a server-authorized payment intent",
)
def create_payment_intent(
    body: InitiatePaymentRequest,
    service: PaymentIntentService = Depends(get_intent_service),
    current_user: User = Depends(get_current_user_strict),
):
    intent = service.initiate(
        buyer=current_user,
        listing_id=body.listing_id,
        idempotency_key=body.idempotency_key,
    )
    import hashlib
    intent.order_id_hex = "0x" + hashlib.sha256(intent.order_id.encode()).hexdigest()
    return intent


@router.get(
    "/intent/{payment_id}",
    response_model=PaymentStatusResponse,
    summary="Get a payment intent's server-authoritative status",
)
def get_payment_intent(
    payment_id: str,
    service: PaymentIntentService = Depends(get_intent_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.get(payment_id, buyer=current_user)


@router.post(
    "/provider/webhook",
    summary="Provider-authenticated payment webhook (idempotent, replay-safe)",
)
async def provider_webhook(
    request: Request,
    x_blip_signature: str | None = Header(None, alias="X-Blip-Signature"),
    x_blip_timestamp: str | None = Header(None, alias="X-Blip-Timestamp"),
    service: PaymentIntentService = Depends(get_intent_service),
):
    raw = await request.body()
    headers = {
        "X-Blip-Signature": x_blip_signature or "",
        "X-Blip-Timestamp": x_blip_timestamp or "",
    }
    order = service.process_webhook(headers=headers, raw_body=raw)
    from app.schemas.order import OrderResponse

    return OrderResponse.model_validate(order)


@router.post(
    "/webhook",
    response_model=OrderResponse,
    summary="Blip Pay payment confirmation webhook",
    description="Validates HMAC-SHA256 signature, enforces idempotency, locks Quai Network smart contract escrow, and transitions order to 'escrow_locked'.",
)
async def handle_blip_webhook(
    request: Request,
    body: BlipPayWebhookPayload,
    x_blip_signature: str | None = Header(None, alias="X-Blip-Signature"),
    x_blip_timestamp: str | None = Header(None, alias="X-Blip-Timestamp"),
    order_service: OrderService = Depends(get_order_service),
):
    raw_body = await request.body()
    if not PaymentService.verify_webhook_signature(
        x_blip_signature, raw_body, timestamp_header=x_blip_timestamp
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Blip Pay webhook HMAC-SHA256 cryptographic signature.",
        )

    return order_service.handle_webhook(
        payment_reference=body.payment_reference,
        blip_status=body.status,
        raw_payload=body.model_dump(),
    )


@router.post(
    "/refund",
    summary="Refund Blip Pay payment and Quai Network escrow",
    description="Processes full refund to buyer, transitions order to 'refunded', restores listing inventory, and logs BlipPaymentRecord audit entry.",
)
def refund_payment(
    order_id: str = Query(..., description="UUID of the order to refund"),
    reason: str | None = Query(None, description="Optional explanation for refund"),
    service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.refund_payment(
        order_id=order_id, actor_id=current_user.id, reason=reason
    )


@router.get(
    "/callback/success",
    summary="Blip Pay payment success browser callback",
    description="Callback endpoint where users are redirected after successful Blip Pay checkout.",
)
def payment_success_callback(
    reference: str = Query(..., description="Unique Blip Pay order reference"),
    service: PaymentService = Depends(get_payment_service),
) -> dict[str, Any]:
    return service.handle_payment_callback(reference=reference, callback_status="success")


@router.get(
    "/callback/failure",
    summary="Blip Pay payment failure browser callback",
    description="Callback endpoint where users are redirected after failed or cancelled Blip Pay checkout.",
)
def payment_failure_callback(
    reference: str = Query(..., description="Unique Blip Pay order reference"),
    service: PaymentService = Depends(get_payment_service),
) -> dict[str, Any]:
    return service.handle_payment_callback(reference=reference, callback_status="failed")


@router.get(
    "/records/order/{order_id}",
    response_model=list[BlipPaymentRecordResponse],
    summary="Get audited Blip Pay payment records for an order",
    description="Returns chronological audit trail of all Blip Pay payment intents and webhooks associated with an order ID.",
)
def get_payment_records_by_order(
    order_id: str,
    service: PaymentService = Depends(get_payment_service),
):
    return service.get_blip_payment_records(order_id)


@router.get(
    "/records/reference/{payment_reference}",
    response_model=BlipPaymentRecordResponse,
    summary="Get Blip Pay payment record by payment reference",
    description="Returns specific Blip Pay payment audit record matching the unique payment reference.",
)
def get_payment_record_by_reference(
    payment_reference: str,
    service: PaymentService = Depends(get_payment_service),
):
    rec = service.get_record_by_reference(payment_reference)
    if not rec:
        raise EntityNotFoundError("BlipPaymentRecord", payment_reference)
    return rec

@router.post(
    "/intent/{payment_id}/confirm",
    response_model=PaymentStatusResponse,
    summary="Confirm an on-chain Quai escrow transaction",
)
def confirm_onchain_payment(
    payment_id: str,
    payload: dict,
    service: PaymentIntentService = Depends(get_intent_service),
    current_user: User = Depends(get_current_user_strict),
):
    tx_hash = (payload or {}).get("tx_hash")
    if not tx_hash:
        raise HTTPException(status_code=400, detail="tx_hash is required.")
    intent = service.confirm_onchain_funding(
        buyer=current_user, payment_id=payment_id, tx_hash=tx_hash
    )
    return intent

