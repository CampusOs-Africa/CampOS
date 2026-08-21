"""Server-authoritative payment intent orchestration.

This service owns payment lifecycle, idempotency, and webhook processing. It
never trusts client-supplied buyer/seller/amount/status.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import CampusOSException, EntityNotFoundError, ForbiddenError
from app.models.marketplace import MarketplaceListing
from app.models.order import Order
from app.models.payment import PaymentIntent, WebhookEvent
from app.models.user import User
from app.repositories.order_repository import OrderRepository
from app.services.order_service import OrderService
from app.services.payment_provider import (
    WebhookEvent as ProviderEvent,
)
from app.services.payment_provider import (
    get_provider,
)

logger = logging.getLogger("campusos.payments")

# Legal payment state machine.
TRANSITIONS: dict[str, set[str]] = {
    "pending": {"processing", "failed", "cancelled", "expired", "paid"},
    "processing": {"paid", "failed", "expired"},
    "paid": {"refunded"},
    "failed": set(),
    "cancelled": set(),
    "expired": set(),
    "refunded": set(),
}


def _now() -> datetime:
    return datetime.now(UTC)


class PaymentIntentService:
    def __init__(self, db: Session):
        self.db = db
        self.orders = OrderRepository(db)
        self.provider = get_provider()

    # ---------------------------------------------------------- create intent
    def initiate(
        self,
        *,
        buyer: User,
        listing_id: str,
        idempotency_key: str | None,
    ) -> PaymentIntent:
        listing = self.db.query(MarketplaceListing).filter(MarketplaceListing.id == listing_id).first()
        if not listing:
            raise EntityNotFoundError("MarketplaceListing", listing_id)
        if listing.status != "active" or listing.inventory_count <= 0:
            raise CampusOSException("Listing is not available.", status_code=400)
        if listing.seller_id == buyer.id:
            raise CampusOSException("You cannot purchase your own listing.", status_code=400)

        # Seller must be a verified student to sell.
        seller = self.db.get(User, listing.seller_id)
        if not seller or seller.verification_status not in ("verified", "approved"):
            raise CampusOSException(
                "This seller is not verified. Purchases are only allowed from verified students.",
                status_code=400,
            )

        # Server-authoritative amount comes from the listing, never the client.
        # On-chain escrow locks native QUAI. listing.price is in QUAI (ether);
        # amount_minor is wei (1 QUAI = 10^18 wei). NGN conversion is not
        # fabricated because no verified NGN->QUAI ramp is available.
        amount_minor = str(int(listing.price * (10**18)))
        idem = (idempotency_key or f"buyer-{buyer.id}-listing-{listing_id}").strip()

        # Any existing intent with this key is a conflict unless it belongs to
        # this exact buyer and represents the same purchase.
        same_key = (
            self.db.query(PaymentIntent)
            .filter(PaymentIntent.idempotency_key == idem)
            .first()
        )
        if same_key and same_key.buyer_id != buyer.id:
            raise CampusOSException(
                "Idempotency key already used by another buyer.",
                status_code=409,
            )
        existing = same_key if same_key and same_key.buyer_id == buyer.id else None
        if existing:
            if existing.order_id and existing.amount_minor == amount_minor and existing.seller_id == listing.seller_id:
                return existing
            raise CampusOSException(
                "Idempotency key conflict: a different payment already exists.",
                status_code=409,
            )

        # Reuse an initiated order for the same buyer+listing (dedup).
        order = self.orders.get_initiated_order(buyer.id, listing_id)
        if not order:
            order = Order(
                buyer_id=buyer.id,
                listing_id=listing.id,
                seller_id=listing.seller_id,
                amount=listing.price,
                payment_reference=f"blip_pay_{uuid.uuid4().hex[:16]}",
                status="initiated",
            )
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)

        intent = PaymentIntent(
            order_id=order.id,
            buyer_id=buyer.id,
            seller_id=listing.seller_id,
            amount_minor=amount_minor,
            currency="NGN",  # display currency
            display_price=str(listing.price),
            display_currency="NGN",
            settlement_asset="QUAI",
            settlement_amount_wei=amount_minor,
            provider=self.provider.name,
            idempotency_key=idem,
            status="pending",
        )
        self.db.add(intent)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            # Concurrent duplicate -> return the existing intent.
            existing = (
                self.db.query(PaymentIntent)
                .filter(
                    PaymentIntent.idempotency_key == idem,
                    PaymentIntent.buyer_id == buyer.id,
                )
                .first()
            )
            if existing:
                return existing
            raise

        self.db.refresh(intent)

        # Ask the provider for a checkout URL (mock in dev; blocked live).
        try:
            result = self.provider.create_payment(
                reference=intent.id,
                amount_minor=amount_minor,
                currency="NGN",
                buyer_email=buyer.email,
            )
            intent.provider_reference = result.provider_reference
            intent.checkout_url = result.checkout_url
            if result.status and result.status != intent.status:
                self._transition(intent, result.status)
            self.db.commit()
            self.db.refresh(intent)
        except CampusOSException as e:
            # Live provider unavailable: record and surface; intent stays pending.
            intent.failure_reason = str(e.message)
            self.db.commit()
            logger.warning("Payment provider unavailable for intent %s: %s", intent.id, e.message)

        return intent


    # ---------------------------------------------------------- on-chain
    def confirm_onchain_funding(
        self, *, buyer: User, payment_id: str, tx_hash: str
    ) -> PaymentIntent:
        """Verify a buyer-submitted escrow funding tx against Quai and mark paid."""
        intent = self.db.get(PaymentIntent, payment_id)
        if not intent:
            raise EntityNotFoundError("PaymentIntent", payment_id)
        if intent.buyer_id != buyer.id and buyer.role != "admin":
            raise ForbiddenError("You cannot confirm this payment.")

        order = self.db.get(Order, intent.order_id)
        if not order:
            raise EntityNotFoundError("Order", intent.order_id)

        from app.services.quai_verification import QuaiVerificationService

        verifier = QuaiVerificationService()
        # The on-chain orderId is the keccak256 of the CampusOS order id,
        # matching how the frontend constructs the escrow.
        import hashlib

        order_id_bytes = hashlib.sha256(order.id.encode()).digest()
        result = verifier.verify_escrow_funding(
            tx_hash=tx_hash,
            expected_order_id=order_id_bytes,
            expected_buyer=intent.buyer_id,
            expected_seller=intent.seller_id,
            expected_amount_minor=intent.amount_minor,
        )
        if result.status.value != "confirmed":
            raise CampusOSException(
                f"On-chain transaction not confirmed (status={result.status.value}).",
                status_code=400,
            )

        # Bind the verified tx and mark payment paid.
        intent.quai_tx_hash = tx_hash
        self._transition(intent, "processing")
        self._transition(intent, "paid")
        intent.paid_at = utc_now()
        self.db.commit()

        # Hand off to the existing order/escrow state machine.
        from app.services.order_service import OrderService

        OrderService(self.db).handle_webhook(
            payment_reference=order.payment_reference,
            blip_status="success",
            raw_payload={"quai_tx_hash": tx_hash, "source": "quai"},
        )
        return intent

    # --------------------------------------------------------------- retrieve
    def get(self, payment_id: str, *, buyer: User) -> PaymentIntent:
        intent = self.db.get(PaymentIntent, payment_id)
        if not intent:
            raise EntityNotFoundError("PaymentIntent", payment_id)
        if intent.buyer_id != buyer.id and buyer.role != "admin":
            raise ForbiddenError("You cannot access this payment.")
        return intent

    def list_for_order(self, order_id: str, *, buyer: User) -> list[PaymentIntent]:
        intents = (
            self.db.query(PaymentIntent)
            .filter(PaymentIntent.order_id == order_id)
            .all()
        )
        if any(i.buyer_id != buyer.id for i in intents) and buyer.role != "admin":
            raise ForbiddenError("You cannot access payments for this order.")
        return intents

    # ----------------------------------------------------------------- webhook
    def process_webhook(self, *, headers: dict[str, str], raw_body: bytes) -> Order:
        event = self.provider.parse_webhook(headers=headers, raw_body=raw_body)

        # Persist the event once (unique provider+event_id) for replay safety.
        payload_hash = hashlib.sha256(raw_body).hexdigest()
        existing = (
            self.db.query(WebhookEvent)
            .filter(
                WebhookEvent.provider == self.provider.name,
                WebhookEvent.event_id == event.event_id,
            )
            .first()
        )
        if existing and existing.status == "processed":
            logger.info("Duplicate webhook event %s ignored", event.event_id)
            order = self.db.get(Order, existing.payment_reference) if existing.payment_reference else None
            return order or self._enrich_existing_for_event(existing)
        if existing:
            return self._enrich_existing_for_event(existing)

        record = WebhookEvent(
            provider=self.provider.name,
            event_id=event.event_id,
            event_type=event.event_type,
            payment_reference=event.payment_reference,
            signature_verified=True,
            payload_hash=payload_hash,
            status="received",
        )
        self.db.add(record)
        self.db.commit()

        try:
            order = self._apply_event(event)
            record.status = "processed"
            record.processed_at = _now()
            record.payment_reference = order.id if order else record.payment_reference
            self.db.commit()
            return order
        except Exception as e:
            self.db.rollback()
            record.processing_error = str(e)[:500]
            record.status = "failed"
            self.db.add(record)
            self.db.commit()
            raise

    def _enrich_existing_for_event(self, record: WebhookEvent) -> Order:
        if record.payment_reference:
            order = self.db.get(Order, record.payment_reference)
            if order:
                return order
        raise CampusOSException("Webhook event could not be resolved.", status_code=400)

    def _apply_event(self, event: ProviderEvent) -> Order:
        if not event.payment_reference:
            raise CampusOSException("Webhook missing payment reference.", status_code=400)

        order = self.orders.get_by_payment_reference(event.payment_reference)
        if not order:
            # Could also be a PaymentIntent id reference; resolve that.
            intent = self.db.get(PaymentIntent, event.payment_reference)
            if not intent:
                raise EntityNotFoundError("Order reference", event.payment_reference)
            order = self.db.get(Order, intent.order_id)

        # Locate the payment intent for this order.
        intent = (
            self.db.query(PaymentIntent)
            .filter(PaymentIntent.order_id == order.id)
            .order_by(PaymentIntent.created_at.desc())
            .first()
        )
        if not intent:
            raise CampusOSException("No payment intent for this order.", status_code=400)

        # Strict server-side verification of financial facts.
        if event.amount_minor is not None and int(event.amount_minor) != int(intent.amount_minor):
            raise CampusOSException(
                "Webhook amount does not match payment intent.", status_code=400
            )
        if event.currency and event.currency.upper() != intent.currency.upper():
            raise CampusOSException("Webhook currency mismatch.", status_code=400)

        provider_status = (event.status or "").lower()
        if provider_status in ("success", "successful", "paid", "completed"):
            self._transition(intent, "paid")
            intent.paid_at = _now()
            intent.provider_reference = event.payment_reference
            self.db.commit()
            # Delegate to existing order/escrow logic: webhook locks escrow.
            return OrderService(self.db).handle_webhook(
                payment_reference=order.payment_reference,
                blip_status="success",
                raw_payload=event.raw,
            )
        if provider_status in ("failed", "failure", "cancelled", "canceled", "expired"):
            target = "cancelled" if "cancel" in provider_status else (
                "expired" if "expired" in provider_status else "failed"
            )
            self._transition(intent, target)
            intent.failure_reason = f"Provider reported {provider_status}"
            self.db.commit()
            return order

        # Unknown/ignored status: do not mutate money state.
        logger.info("Unhandled provider status '%s'; no state change", provider_status)
        return order

    # ----------------------------------------------------------- state machine
    def _transition(self, intent: PaymentIntent, new_status: str) -> None:
        allowed = TRANSITIONS.get(intent.status, set())
        if new_status not in allowed and new_status != intent.status:
            raise CampusOSException(
                f"Invalid payment transition {intent.status} -> {new_status}",
                status_code=400,
            )
        intent.status = new_status
