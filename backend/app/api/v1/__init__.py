from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.escrow import router as escrow_router
from app.api.v1.fraud import router as fraud_router
from app.api.v1.marketplace import router as marketplace_router
from app.api.v1.orders import router as orders_router
from app.api.v1.payments import router as payments_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.trust import router as trust_router
from app.api.v1.users import router as users_router
from app.api.v1.verification import router as verification_router
from app.api.v1.wallet import router as wallet_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(verification_router)
api_router.include_router(users_router)
api_router.include_router(wallet_router)
api_router.include_router(marketplace_router)
api_router.include_router(payments_router)
api_router.include_router(orders_router)
api_router.include_router(escrow_router)
api_router.include_router(reviews_router)
api_router.include_router(trust_router)
api_router.include_router(fraud_router)
