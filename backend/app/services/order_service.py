import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.cache import invalidate_marketplace_cache
from app.core.exceptions import CampusOSException, EntityNotFoundError, ForbiddenError
from app.models.order import BlipPaymentRecord, Order, OrderItem
from app.models.transaction import Transaction
from app.repositories.marketplace_repository import MarketplaceRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.escrow import EscrowCreateRequest
from app.schemas.order import OrderCreateRequest, OrderResponse
from app.services.escrow_service import EscrowService
from app.services.payment_service import PaymentService
from app.services.trust_service import TrustService

logger = logging.getLogger("campusos.orders")


def utc_now():
    return datetime.now(UTC)


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.listing_repo = MarketplaceRepository(db)
        self.user_repo = UserRepository(db)
        self.tx_repo = TransactionRepository(db)
        self.trust_service = TrustService(db)
        self.escrow_service = EscrowService(db)

    def _enrich_order(self, order) -> OrderResponse:
        res = OrderResponse.model_validate(order)
        listing = self.listing_repo.get_by_id(order.listing_id)
        buyer = self.user_repo.get_by_id(order.buyer_id)
        seller = self.user_repo.get_by_id(order.seller_id)
        if listing:
            res.listing_title = listing.title
        if buyer:
            res.buyer_name = buyer.name
        if seller:
            res.seller_name = seller.name
        return res

    def create_order(self, req: OrderCreateRequest) -> OrderResponse:
        buyer = self.user_repo.get_by_id(req.buyer_id)
        if not buyer:
            raise EntityNotFoundError("User", req.buyer_id)

        listing = self.listing_repo.get_by_id(req.listing_id)
        if not listing:
            raise EntityNotFoundError("MarketplaceListing", req.listing_id)

        if listing.status != "active" or listing.inventory_count < req.quantity:
            raise CampusOSException(
                "Marketplace listing is out of stock or no longer active.",
                status_code=400,
            )

        if listing.seller_id == req.buyer_id:
            raise CampusOSException(
                "You cannot purchase your own marketplace listing.",
                status_code=400,
            )

        reference = f"blip_pay_{uuid.uuid4().hex[:16]}"
        order = Order(
            buyer_id=req.buyer_id,
            listing_id=req.listing_id,
            seller_id=listing.seller_id,
            amount=req.amount,
            payment_reference=reference,
            status="initiated",
        )
        created_order = self.order_repo.create(order)

        item = OrderItem(
            order_id=created_order.id,
            listing_id=listing.id,
            seller_id=listing.seller_id,
            quantity=req.quantity,
            price_per_unit=listing.price,
            subtotal=req.amount,
        )
        self.order_repo.create_item(item)

        return self._enrich_order(created_order)

    def get_order_by_id(self, order_id: str) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundError("Order", order_id)
        return self._enrich_order(order)

    def get_orders_by_buyer(self, buyer_id: str, skip: int = 0, limit: int = 20) -> list[OrderResponse]:
        orders = self.order_repo.get_by_buyer(buyer_id, skip=skip, limit=limit)
        return [self._enrich_order(o) for o in orders]

    def get_orders_by_seller(self, seller_id: str, skip: int = 0, limit: int = 20) -> list[OrderResponse]:
        orders = self.order_repo.get_by_seller(seller_id, skip=skip, limit=limit)
        return [self._enrich_order(o) for o in orders]

    def handle_webhook(
        self, payment_reference: str, blip_status: str, raw_payload: dict | None = None
    ) -> OrderResponse:
        is_replayed = PaymentService.check_and_cache_webhook_replay(
            payment_reference
        )
        order = self.order_repo.get_by_payment_reference(payment_reference)
        if not order:
            raise EntityNotFoundError("Order reference", payment_reference)

        if is_replayed or order.status != "initiated":
            logger.info(
                f"Duplicate/replayed Blip Pay webhook for order {order.id} (status: {order.status}); ignoring."
            )
            return self._enrich_order(order)

        if blip_status.lower() != "success":
            order.status = "failed"
            self.order_repo.update(order)
            return self._enrich_order(order)

        order.status = "escrow_locked"
        order.escrow_tx_hash = f"0xquai_escrow_lock_{uuid.uuid4().hex[:16]}"
        self.order_repo.update(order)

        blip_rec = BlipPaymentRecord(
            order_id=order.id,
            user_id=order.buyer_id,
            payment_reference=payment_reference,
            amount=order.amount,
            currency="NGN",
            status="successful",
            raw_webhook_payload=raw_payload,
        )
        self.order_repo.create_blip_record(blip_rec)

        self.escrow_service.create_escrow(
            EscrowCreateRequest(
                order_id=order.id,
                buyer_id=order.buyer_id,
                seller_id=order.seller_id,
                amount=order.amount,
            )
        )

        listing = self.listing_repo.get_by_id(order.listing_id)
        if listing:
            listing.inventory_count = max(0, listing.inventory_count - 1)
            if listing.inventory_count == 0:
                listing.status = "pending_order"
            self.listing_repo.update(listing)
        invalidate_marketplace_cache()

        logger.info(
            f"Order {order.id} escrow locked on Quai Network (Tx: {order.escrow_tx_hash})"
        )
        return self._enrich_order(order)

    def confirm_shipment(self, order_id: str, actor_id: str) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundError("Order", order_id)

        if actor_id != order.seller_id:
            raise ForbiddenError("Only the seller can confirm shipment.")

        if order.status not in ("escrow_locked", "escrow_funded"):
            raise CampusOSException(
                f"Cannot confirm shipment for order in status '{order.status}'.",
                status_code=400,
            )

        order.status = "shipped_pending_delivery"
        self.order_repo.update(order)
        logger.info(
            f"Order {order.id} marked as shipped by seller {actor_id}"
        )
        return self._enrich_order(order)

    def confirm_delivery(self, order_id: str, actor_id: str) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundError("Order", order_id)

        if actor_id not in (order.buyer_id, order.seller_id):
            raise ForbiddenError("Only the buyer or seller can confirm delivery.")

        if order.status not in ("escrow_locked", "escrow_funded", "shipped_pending_delivery"):
            raise CampusOSException(
                f"Cannot confirm delivery for order in status '{order.status}'.",
                status_code=400,
            )

        order.status = "delivered_pending_release"
        self.order_repo.update(order)
        return self._enrich_order(order)

    def release_escrow(self, order_id: str, actor_id: str) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundError("Order", order_id)

        actor = self.user_repo.get_by_id(actor_id)
        if order.buyer_id != actor_id and (not actor or actor.role != "admin"):
            raise ForbiddenError(
                "Only the buyer or an administrator can release escrow funds."
            )

        if order.status not in (
            "escrow_locked",
            "escrow_funded",
            "shipped_pending_delivery",
            "delivered_pending_release",
            "disputed",
        ):
            raise CampusOSException(
                f"Cannot release escrow for order in status '{order.status}'.",
                status_code=400,
            )

        order.status = "completed"
        order.completed_at = utc_now()
        order.escrow_tx_hash = f"0xquai_escrow_release_{uuid.uuid4().hex[:16]}"
        self.order_repo.update(order)

        self.escrow_service.release_escrow(order.id, actor_id)

        listing = self.listing_repo.get_by_id(order.listing_id)
        if listing and listing.inventory_count == 0:
            listing.status = "sold"
            self.listing_repo.update(listing)
        invalidate_marketplace_cache()

        self.trust_service.award_order_completion_bonus(
            order.buyer_id, order.seller_id, order.id
        )

        buyer_user = self.user_repo.get_by_id(order.buyer_id)
        seller_user = self.user_repo.get_by_id(order.seller_id)

        b_addr = buyer_user.wallet_address if (buyer_user and buyer_user.wallet_address) else "0xBuyerQuaiWallet0001"
        s_addr = seller_user.wallet_address if (seller_user and seller_user.wallet_address) else "0xSellerQuaiWallet0001"

        tx_out = Transaction(
            user_id=order.buyer_id,
            wallet_address=b_addr,
            recipient_address=s_addr,
            amount=order.amount,
            tx_hash=f"{order.escrow_tx_hash}_buy",
            type="send",
            status="confirmed",
            network="Quai Network Testnet (Chain ID 9000)",
            block_number=1,
            note=f"Marketplace purchase: {order.id}",
        )
        self.tx_repo.create(tx_out)

        tx_in = Transaction(
            user_id=order.seller_id,
            wallet_address=s_addr,
            recipient_address=b_addr,
            amount=order.amount,
            tx_hash=f"{order.escrow_tx_hash}_sell",
            type="receive",
            status="confirmed",
            network="Quai Network Testnet (Chain ID 9000)",
            block_number=1,
            note=f"Marketplace sale: {order.id}",
        )
        self.tx_repo.create(tx_in)

        logger.info(
            f"Escrow released for order {order.id}. +5 Trust Score awarded to Buyer and Seller."
        )
        return self._enrich_order(order)

    def dispute_order(
        self, order_id: str, actor_id: str, reason: str
    ) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundError("Order", order_id)

        if actor_id not in (order.buyer_id, order.seller_id):
            raise ForbiddenError("Only the buyer or seller can dispute an order.")

        if order.status not in ("escrow_locked", "escrow_funded", "shipped_pending_delivery", "delivered_pending_release"):
            raise CampusOSException(
                f"Cannot dispute order in status '{order.status}'.",
                status_code=400,
            )

        order.status = "disputed"
        self.order_repo.update(order)
        self.escrow_service.dispute_escrow(order.id, actor_id, reason)
        logger.warning(
            f"Order {order.id} disputed by user {actor_id}: {reason}"
        )
        return self._enrich_order(order)

    def cancel_order(self, order_id: str, actor_id: str) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundError("Order", order_id)

        actor = self.user_repo.get_by_id(actor_id)
        if actor_id not in (order.buyer_id, order.seller_id) and (
            not actor or actor.role != "admin"
        ):
            raise ForbiddenError("Only order participants or admin can cancel.")

        if order.status not in ("initiated", "escrow_locked", "escrow_funded"):
            raise CampusOSException(
                f"Cannot cancel order in status '{order.status}'.", status_code=400
            )

        order.status = "cancelled"
        self.order_repo.update(order)
        return self._enrich_order(order)
