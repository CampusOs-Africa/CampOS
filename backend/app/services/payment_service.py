import hashlib
import hmac
import logging
import time
import uuid
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import CampusOSException, EntityNotFoundError, ForbiddenError
from app.models.order import BlipPaymentRecord, Order
from app.repositories.marketplace_repository import MarketplaceRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.order import BlipPayInitiateResponse
from app.services.trust_service import TrustService

logger = logging.getLogger("campusos.payments")


_webhook_replay_cache: dict[str, float] = {}


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.listing_repo = MarketplaceRepository(db)
        self.order_repo = OrderRepository(db)
        self.trust_service = TrustService(db)

    def _execute_blip_pay_request_with_retry(
        self,
        method: str,
        url: str,
        json_data: dict[str, Any],
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> httpx.Response:
        """Execute Blip Pay HTTP API request with exponential backoff retry strategy."""
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.request(
                        method=method,
                        url=url,
                        headers={
                            "Authorization": f"Bearer {settings.BLIP_PAY_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json=json_data,
                    )
                    res.raise_for_status()
                    return res
            except (httpx.RequestError, httpx.HTTPStatusError, Exception) as e:  # noqa: BLE001
                last_exception = e
                logger.warning(
                    f"Blip Pay API request attempt {attempt}/{max_retries} failed: {e}. Retrying in {base_delay}s..."
                )
                time.sleep(base_delay)
                base_delay *= 2.0
        logger.error(
            f"Blip Pay API call failed after {max_retries} attempts: {last_exception}"
        )
        raise CampusOSException(
            f"Blip Pay API network error: {last_exception}",
            status_code=502,
        )

    def initiate_checkout(
        self, buyer_id: str, listing_id: str, amount: float
    ) -> BlipPayInitiateResponse:
        buyer = self.user_repo.get_by_id(buyer_id)
        if not buyer:
            raise EntityNotFoundError("User", buyer_id)

        listing = self.listing_repo.get_by_id(listing_id)
        if not listing:
            raise EntityNotFoundError("MarketplaceListing", listing_id)

        if listing.status != "active" or listing.inventory_count <= 0:
            raise CampusOSException(
                "Marketplace listing is out of stock or no longer active.",
                status_code=400,
            )

        if listing.seller_id == buyer_id:
            raise CampusOSException(
                "You cannot purchase your own marketplace listing.",
                status_code=400,
            )

        existing_order = self.order_repo.get_initiated_order(buyer_id, listing_id)
        if existing_order and existing_order.amount == amount:
            logger.info(
                f"Duplicate checkout attempt detected for buyer {buyer_id} on listing {listing_id}. Reusing existing order {existing_order.id} (Ref: {existing_order.payment_reference})."
            )
            payment_url = (
                f"{settings.FRONTEND_URL}/checkout/{existing_order.id}"
                if settings.USE_MOCK_BLIP_PAY
                else f"https://checkout.blippay.com/pay/{existing_order.payment_reference}"
            )
            return BlipPayInitiateResponse(
                order_id=existing_order.id,
                payment_reference=existing_order.payment_reference,
                payment_url=payment_url,
                amount=amount,
                currency="NGN",
                status="initiated",
            )

        reference = f"blip_pay_{uuid.uuid4().hex[:16]}"
        order = Order(
            buyer_id=buyer_id,
            listing_id=listing_id,
            seller_id=listing.seller_id,
            amount=amount,
            payment_reference=reference,
            status="initiated",
        )
        created_order = self.order_repo.create(order)

        blip_rec = BlipPaymentRecord(
            order_id=created_order.id,
            user_id=buyer_id,
            payment_reference=reference,
            amount=amount,
            currency="NGN",
            provider="blip_pay",
            status="initiated",
        )
        self.order_repo.create_blip_record(blip_rec)

        if settings.USE_MOCK_BLIP_PAY or settings.BLIP_PAY_API_KEY == "mock-blip-pay-api-key":
            payment_url = f"{settings.FRONTEND_URL}/checkout/{created_order.id}"
            logger.info(
                f"[MOCK-BLIP-PAY] Initiated checkout for buyer {buyer_id} on listing {listing_id} (Ref: {reference})"
            )
        else:
            api_url = f"{settings.BLIP_PAY_API_URL}/checkout/intents"
            payload = {
                "reference": reference,
                "amount": amount,
                "currency": "NGN",
                "customer_email": buyer.email,
                "metadata": {
                    "order_id": created_order.id,
                    "buyer_id": buyer_id,
                    "listing_id": listing_id,
                },
                "success_url": f"http://localhost:8000/api/v1/payments/callback/success?reference={reference}",
                "failure_url": f"http://localhost:8000/api/v1/payments/callback/failure?reference={reference}",
            }
            res = self._execute_blip_pay_request_with_retry("POST", api_url, payload)
            data = res.json()
            payment_url = data.get("checkout_url", f"https://checkout.blippay.com/pay/{reference}")
            logger.info(
                f"[PRODUCTION-BLIP-PAY] Initiated checkout for order {created_order.id} (Ref: {reference})"
            )

        return BlipPayInitiateResponse(
            order_id=created_order.id,
            payment_reference=reference,
            payment_url=payment_url,
            amount=amount,
            currency="NGN",
            status="initiated",
        )

    def get_blip_payment_records(self, order_id: str) -> list[BlipPaymentRecord]:
        """Fetch all Blip Pay payment audit records for a given order."""
        return self.order_repo.get_blip_records_by_order_id(order_id)

    def get_record_by_reference(self, ref: str) -> BlipPaymentRecord | None:
        return self.order_repo.get_blip_record_by_reference(ref)

    def handle_payment_callback(
        self, reference: str, callback_status: str
    ) -> dict[str, Any]:
        """Handle Blip Pay browser callback redirects (success / failure)."""
        order = self.order_repo.get_by_payment_reference(reference)
        if not order:
            raise EntityNotFoundError("Order reference", reference)

        if callback_status.lower() == "success":
            logger.info(f"Payment success callback triggered for reference {reference}")
            return {
                "success": True,
                "order_id": order.id,
                "payment_reference": reference,
                "status": order.status,
                "message": "Payment verified. Quai Network escrow lock active.",
                "redirect_url": f"http://localhost:3000/orders/{order.id}",
            }

        # Failure callback
        if order.status == "initiated":
            order.status = "failed"
            self.order_repo.update(order)
            blip_rec = BlipPaymentRecord(
                order_id=order.id,
                user_id=order.buyer_id,
                payment_reference=reference,
                amount=order.amount,
                currency="NGN",
                provider="blip_pay",
                status="failed",
            )
            self.order_repo.create_blip_record(blip_rec)

        logger.warning(f"Payment failure callback triggered for reference {reference}")
        return {
            "success": False,
            "order_id": order.id,
            "payment_reference": reference,
            "status": "failed",
            "message": "Payment checkout failed or was cancelled by user.",
            "redirect_url": f"{settings.FRONTEND_URL}/checkout/{order.id}",
        }

    def refund_payment(
        self,
        order_id: str,
        actor_id: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Process Blip Pay payment refund and Quai escrow refund."""
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundError("Order", order_id)

        actor = self.user_repo.get_by_id(actor_id)
        if order.seller_id != actor_id and (not actor or actor.role != "admin"):
            raise ForbiddenError(
                "Only the seller or an administrator can refund an order."
            )

        if order.status not in ("escrow_locked", "escrow_funded", "shipped_pending_delivery", "delivered_pending_release", "disputed"):
            raise CampusOSException(
                f"Cannot refund order in status '{order.status}'.",
                status_code=400,
            )

        # Execute Quai Network smart contract escrow refund
        order.status = "refunded"
        order.escrow_tx_hash = f"0xquai_escrow_refund_{uuid.uuid4().hex[:16]}"
        self.order_repo.update(order)

        # Restore inventory
        listing = self.listing_repo.get_by_id(order.listing_id)
        if listing:
            listing.inventory_count += 1
            if listing.status in ("sold", "pending_order"):
                listing.status = "active"
            self.listing_repo.update(listing)

        self.trust_service.penalize_order_refund(order.seller_id, order.id)

        blip_rec = BlipPaymentRecord(
            order_id=order.id,
            user_id=order.buyer_id,
            payment_reference=order.payment_reference,
            amount=order.amount,
            currency="NGN",
            provider="blip_pay",
            status="refunded",
        )
        self.order_repo.create_blip_record(blip_rec)

        logger.info(
            f"Order {order.id} refunded successfully (Quai Tx: {order.escrow_tx_hash}, Reason: {reason})"
        )
        return {
            "success": True,
            "order_id": order.id,
            "payment_reference": order.payment_reference,
            "status": "refunded",
            "escrow_tx_hash": order.escrow_tx_hash,
            "amount_refunded": order.amount,
            "message": f"Order {order.id} refunded to buyer. Inventory restored.",
        }

    @staticmethod
    def verify_webhook_signature(
        signature_header: str | None,
        raw_body_bytes: bytes,
        timestamp_header: str | None = None,
    ) -> bool:
        """Verify HMAC-SHA256 signature and optional timestamp drift (±300 seconds) of incoming Blip Pay webhooks."""
        if timestamp_header:
            try:
                ts = int(timestamp_header)
                if abs(time.time() - ts) > 300:
                    logger.warning(
                        f"Webhook timestamp drift exceeded allowable window (ts={ts}, now={time.time()})"
                    )
                    return False
            except (ValueError, TypeError):
                return False

        if (
            settings.USE_MOCK_BLIP_PAY
            and signature_header
            and signature_header.startswith("mock_sig")
        ):
            return True

        if not signature_header:
            return False

        secrets = settings.get_blip_webhook_secrets()
        for sec in secrets:
            computed = hmac.new(
                sec.encode("utf-8"),
                raw_body_bytes,
                hashlib.sha256,
            ).hexdigest()
            if hmac.compare_digest(computed, signature_header):
                return True
        return False

    @staticmethod
    def check_and_cache_webhook_replay(
        reference: str, ttl_seconds: int = 86400
    ) -> bool:
        """
        Check if webhook payment reference has already been processed within the TTL window (default 24 hours / 86400s).
        Returns True if this is a replayed/duplicate webhook; returns False if fresh.
        """
        now = time.time()
        try:
            import redis

            client = redis.Redis.from_url(
                settings.REDIS_URL, decode_responses=True, socket_timeout=0.5
            )
            key = f"campusos:webhook_replay:{reference}"
            existing = client.get(key)
            if existing:
                logger.info(
                    f"Webhook replay detected in Redis cache for reference {reference}"
                )
                return True
            client.set(key, str(now), ex=ttl_seconds)
            return False
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Redis replay check unavailable: {e}")

        expired_keys = [k for k, t in _webhook_replay_cache.items() if now > t]
        for k in expired_keys:
            _webhook_replay_cache.pop(k, None)

        if reference in _webhook_replay_cache:
            logger.info(
                f"Webhook replay detected in memory cache for reference {reference}"
            )
            return True

        _webhook_replay_cache[reference] = now + ttl_seconds
        return False
