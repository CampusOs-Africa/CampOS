from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_strict
from app.models.user import User
from app.schemas.order import (
    OrderCreateRequest,
    OrderDisputeRequest,
    OrderResponse,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders & Quai Escrow"])


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(db=db)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=201,
    summary="Create a new marketplace order",
    description="Creates a new order. The buyer is always derived from the authenticated JWT.",
)
@router.post(
    "/",
    response_model=OrderResponse,
    status_code=201,
    summary="Create a new marketplace order",
    description="Creates a new order. The buyer is always derived from the authenticated JWT.",
)
def create_order(
    body: OrderCreateRequest,
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user_strict),
):
    # The authenticated user is always the buyer; a client-supplied buyer_id
    # can never place an order on behalf of another user.
    body.buyer_id = current_user.id
    return service.create_order(body)


def _can_access(user: User, order) -> bool:
    return (
        user.role == "admin"
        or order.buyer_id == user.id
        or order.seller_id == user.id
    )


@router.get(
    "/history",
    response_model=list[OrderResponse],
    summary="Get paginated order history for the current user",
)
def get_order_history(
    role: str = Query("all", description="Filter by role ('buyer', 'seller', 'all')"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user_strict),
):
    user_id = current_user.id
    if role.lower() == "buyer":
        return service.get_orders_by_buyer(user_id, skip=skip, limit=limit)
    if role.lower() == "seller":
        return service.get_orders_by_seller(user_id, skip=skip, limit=limit)
    buyer_orders = service.get_orders_by_buyer(user_id, skip=0, limit=100)
    seller_orders = service.get_orders_by_seller(user_id, skip=0, limit=100)
    combined = {o.id: o for o in buyer_orders + seller_orders}
    sorted_list = sorted(
        combined.values(), key=lambda x: x.created_at, reverse=True
    )
    return sorted_list[skip : skip + limit]


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID (buyer, seller, or admin only)",
)
def get_order_by_id(
    order_id: str,
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user_strict),
):
    order = service.get_order_by_id(order_id)
    if not _can_access(current_user, order):
        raise HTTPException(status_code=403, detail="You cannot access this order.")
    return order


@router.get(
    "/buyer/{buyer_id}",
    response_model=list[OrderResponse],
    summary="Get paginated orders for buyer (self or admin)",
)
def get_orders_by_buyer(
    buyer_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user_strict),
):
    if current_user.id != buyer_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You cannot access these orders.")
    return service.get_orders_by_buyer(buyer_id=buyer_id, skip=skip, limit=limit)


@router.get(
    "/seller/{seller_id}",
    response_model=list[OrderResponse],
    summary="Get paginated orders for seller (self or admin)",
)
def get_orders_by_seller(
    seller_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user_strict),
):
    if current_user.id != seller_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You cannot access these orders.")
    return service.get_orders_by_seller(
        seller_id=seller_id, skip=skip, limit=limit
    )


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel marketplace order",
)
def cancel_order(
    order_id: str,
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.cancel_order(order_id=order_id, actor_id=current_user.id)


@router.post(
    "/{order_id}/confirm-shipment",
    response_model=OrderResponse,
    summary="Confirm shipment of order item (seller only)",
)
def confirm_shipment(
    order_id: str,
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.confirm_shipment(order_id=order_id, actor_id=current_user.id)


@router.post(
    "/{order_id}/confirm-delivery",
    response_model=OrderResponse,
    summary="Confirm physical delivery (buyer/seller)",
)
def confirm_delivery(
    order_id: str,
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.confirm_delivery(order_id=order_id, actor_id=current_user.id)


@router.post(
    "/{order_id}/release-escrow",
    response_model=OrderResponse,
    summary="Release Quai escrow (buyer or admin)",
)
def release_escrow(
    order_id: str,
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.release_escrow(order_id=order_id, actor_id=current_user.id)


@router.post(
    "/{order_id}/dispute",
    response_model=OrderResponse,
    summary="Dispute marketplace order (buyer/seller)",
)
def dispute_order(
    order_id: str,
    body: OrderDisputeRequest,
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.dispute_order(
        order_id=order_id, actor_id=current_user.id, reason=body.reason
    )
