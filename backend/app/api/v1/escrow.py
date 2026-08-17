from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_strict
from app.models.user import User
from app.schemas.escrow import (
    EscrowActionRequest,
    EscrowCreateRequest,
    EscrowRecordResponse,
)
from app.services.escrow_service import EscrowService

router = APIRouter(prefix="/escrow", tags=["Quai Smart Contract Escrow"])


def get_escrow_service(db: Session = Depends(get_db)) -> EscrowService:
    return EscrowService(db=db)


@router.post(
    "/create",
    response_model=EscrowRecordResponse,
    status_code=201,
    summary="Create an escrow record and lock on Quai Network",
)
def create_escrow(
    body: EscrowCreateRequest,
    service: EscrowService = Depends(get_escrow_service),
    current_user: User = Depends(get_current_user_strict),
):
    # Only the buyer (derived from JWT) may create an escrow for their order.
    body.buyer_id = current_user.id
    return service.create_escrow(body)


@router.post(
    "/deposit",
    response_model=EscrowRecordResponse,
    summary="Deposit funds into escrow (buyer or admin)",
)
def deposit_escrow(
    body: EscrowActionRequest,
    service: EscrowService = Depends(get_escrow_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.deposit_escrow(
        order_id=body.order_id, actor_id=current_user.id
    )


@router.post(
    "/release",
    response_model=EscrowRecordResponse,
    summary="Release escrow funds to seller (buyer or admin)",
)
def release_escrow(
    body: EscrowActionRequest,
    service: EscrowService = Depends(get_escrow_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.release_escrow(
        order_id=body.order_id, actor_id=current_user.id
    )


@router.post(
    "/refund",
    response_model=EscrowRecordResponse,
    summary="Refund escrow funds to buyer (seller or admin)",
)
def refund_escrow(
    body: EscrowActionRequest,
    service: EscrowService = Depends(get_escrow_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.refund_escrow(
        order_id=body.order_id,
        actor_id=current_user.id,
        reason=body.reason,
    )


@router.post(
    "/dispute",
    response_model=EscrowRecordResponse,
    summary="Dispute escrow transaction (participants)",
)
def dispute_escrow(
    body: EscrowActionRequest,
    service: EscrowService = Depends(get_escrow_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.dispute_escrow(
        order_id=body.order_id,
        actor_id=current_user.id,
        reason=body.reason,
    )


@router.get(
    "/{id}",
    response_model=EscrowRecordResponse,
    summary="Get escrow details by ID or order ID",
)
def get_escrow_by_id(
    id: str,
    service: EscrowService = Depends(get_escrow_service),
    current_user: User = Depends(get_current_user_strict),
):
    escrow = service.get_escrow(id)
    if (
        current_user.role != "admin"
        and current_user.id not in (escrow.buyer_id, escrow.seller_id)
    ):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="You cannot access this escrow.")
    return escrow
