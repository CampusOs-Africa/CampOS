from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_strict
from app.models.user import User
from app.schemas.wallet import (
    TransactionResponse,
    WalletBalanceResponse,
    WalletConnectRequest,
    WalletConnectResponse,
    WalletDashboardResponse,
    WalletSendRequest,
    WalletSendResponse,
)
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/wallet", tags=["Campus Wallet (Quai Network)"])


def get_wallet_service(db: Session = Depends(get_db)) -> WalletService:
    return WalletService(db=db)


@router.post(
    "/connect",
    response_model=WalletConnectResponse,
    status_code=200,
    summary="Connect and bind a Quai EVM wallet to the authenticated account",
)
async def connect_wallet(
    body: WalletConnectRequest,
    service: WalletService = Depends(get_wallet_service),
    current_user: User = Depends(get_current_user_strict),
):
    # Wallet is bound to the authenticated user, never a client-supplied id.
    body.user_id = current_user.id
    return await service.connect_wallet(body)


@router.get(
    "/balance",
    response_model=WalletBalanceResponse,
    summary="Get wallet balance",
)
async def get_wallet_balance(
    wallet_address: str | None = Query(
        None, description="Quai EVM address (public on-chain lookup)"
    ),
    service: WalletService = Depends(get_wallet_service),
    current_user: User = Depends(get_current_user_strict),
):
    # Looking up a raw on-chain address is public; looking up by user_id always
    # resolves to the authenticated user's own account.
    return await service.get_balance(
        user_id=current_user.id, wallet_address=wallet_address
    )


@router.get(
    "/history",
    response_model=list[TransactionResponse],
    summary="Get transaction history for the authenticated user",
)
def get_wallet_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: WalletService = Depends(get_wallet_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.get_history(user_id=current_user.id, skip=skip, limit=limit)


@router.post(
    "/send",
    response_model=WalletSendResponse,
    summary="Send QUAI from the authenticated wallet",
)
async def send_quai(
    body: WalletSendRequest,
    service: WalletService = Depends(get_wallet_service),
    current_user: User = Depends(get_current_user_strict),
):
    # Sender is always derived from the JWT to prevent draining others' funds.
    body.sender_id = current_user.id
    return await service.send_quai(body)


@router.get(
    "/dashboard/{user_id}",
    response_model=WalletDashboardResponse,
    summary="Get wallet dashboard (self or admin)",
)
async def get_wallet_dashboard(
    user_id: str,
    service: WalletService = Depends(get_wallet_service),
    current_user: User = Depends(get_current_user_strict),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="You cannot access this wallet dashboard."
        )
    return await service.get_dashboard(user_id)
