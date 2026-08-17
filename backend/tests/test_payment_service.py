import hashlib
import hmac

import pytest

from app.core.config import settings
from app.core.exceptions import CampusOSException
from app.models.marketplace import MarketplaceListing
from app.models.user import User
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService


def test_blip_pay_checkout_duplicate_protection_and_hmac_verification(db_session):
    buyer = User(
        id="buyer-01",
        name="Chidi Okafor",
        email="chidi@unijos.edu.ng",
        verification_status="verified",
    )
    seller = User(
        id="seller-01",
        name="Amina Bello",
        email="amina@unijos.edu.ng",
        verification_status="verified",
        role="admin",
    )
    db_session.add(buyer)
    db_session.add(seller)
    db_session.commit()

    listing = MarketplaceListing(
        id="listing-01",
        seller_id="seller-01",
        title="Engineering Textbook",
        description="Math book",
        category="books",
        price=3500.0,
        images=["https://res.cloudinary.com/test.jpg"],
        status="active",
        inventory_count=1,
    )
    db_session.add(listing)
    db_session.commit()

    service = PaymentService(db=db_session)
    order_service = OrderService(db=db_session)

    # 1. Buyer cannot buy own listing
    with pytest.raises(CampusOSException) as exc_info:
        service.initiate_checkout(
            buyer_id="seller-01", listing_id="listing-01", amount=3500.0
        )
    assert "cannot purchase your own" in str(exc_info.value)

    # 2. Buyer initiates checkout successfully
    checkout = service.initiate_checkout(
        buyer_id="buyer-01", listing_id="listing-01", amount=3500.0
    )
    assert checkout.order_id is not None
    assert checkout.payment_reference.startswith("blip_pay_")
    assert checkout.amount == 3500.0

    # 3. Test duplicate payment protection (submitting second checkout for same buyer & listing reuses existing order)
    checkout_retry = service.initiate_checkout(
        buyer_id="buyer-01", listing_id="listing-01", amount=3500.0
    )
    assert checkout_retry.order_id == checkout.order_id
    assert checkout_retry.payment_reference == checkout.payment_reference

    # 4. Test HMAC-SHA256 Webhook Signature Verification
    body_bytes = b'{"payment_reference":"blip_pay_test","status":"success"}'
    valid_sig = hmac.new(
        settings.BLIP_PAY_WEBHOOK_SECRET.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()

    assert PaymentService.verify_webhook_signature(valid_sig, body_bytes) is True
    assert (
        PaymentService.verify_webhook_signature("invalid_signature_hex", body_bytes)
        is False
    )

    # 5. Simulate Blip Pay Success Webhook (locks escrow)
    locked_order = order_service.handle_webhook(
        payment_reference=checkout.payment_reference,
        blip_status="success",
        raw_payload={"amount": 3500.0, "status": "success"},
    )
    assert locked_order.status == "escrow_locked"
    assert locked_order.escrow_tx_hash is not None

    # 6. Check Idempotency: duplicate success webhook does not duplicate state or fail
    repeat_order = order_service.handle_webhook(
        payment_reference=checkout.payment_reference,
        blip_status="success",
        raw_payload={"amount": 3500.0, "status": "success"},
    )
    assert repeat_order.status == "escrow_locked"

    # 7. Check payment records audit trail
    records = service.get_blip_payment_records(checkout.order_id)
    assert len(records) == 2  # initiated + successful
    statuses = [r.status for r in records]
    assert "initiated" in statuses
    assert "successful" in statuses

    # 8. Test browser success callback redirect helper
    cb_success = service.handle_payment_callback(
        reference=checkout.payment_reference, callback_status="success"
    )
    assert cb_success["success"] is True
    assert "/orders/" in cb_success["redirect_url"]

    # 9. Test payment refund (by seller/admin) & inventory restoration
    refund_res = service.refund_payment(
        order_id=checkout.order_id, actor_id="seller-01", reason="Item out of stock"
    )
    assert refund_res["success"] is True
    assert refund_res["status"] == "refunded"
    assert refund_res["escrow_tx_hash"].startswith("0xquai_escrow_refund_")

    db_session.refresh(listing)
    assert listing.inventory_count == 1  # Restored from 0 -> 1
    assert listing.status == "active"


def test_blip_pay_failure_callback(db_session):
    buyer = User(id="buyer-02", name="Buyer 2", email="b2@unijos.edu.ng")
    seller = User(id="seller-02", name="Seller 2", email="s2@unijos.edu.ng")
    db_session.add(buyer)
    db_session.add(seller)
    db_session.commit()

    listing = MarketplaceListing(
        id="listing-02",
        seller_id="seller-02",
        title="Physics Book",
        description="Physics",
        category="books",
        price=2000.0,
        images=["https://res.cloudinary.com/test.jpg"],
        status="active",
        inventory_count=1,
    )
    db_session.add(listing)
    db_session.commit()

    service = PaymentService(db=db_session)
    checkout = service.initiate_checkout(
        buyer_id="buyer-02", listing_id="listing-02", amount=2000.0
    )

    cb_failure = service.handle_payment_callback(
        reference=checkout.payment_reference, callback_status="failed"
    )
    assert cb_failure["success"] is False
    assert cb_failure["status"] == "failed"

    records = service.get_blip_payment_records(checkout.order_id)
    assert len(records) == 2  # initiated + failed
    assert records[0].status == "failed"
