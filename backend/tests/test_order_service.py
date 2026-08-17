from app.models.marketplace import MarketplaceListing
from app.models.user import User
from app.schemas.order import OrderCreateRequest
from app.schemas.review import ReviewCreateRequest
from app.services.order_service import OrderService
from app.services.review_service import ReviewService


def test_order_escrow_lifecycle_and_trust_rewards(db_session):
    buyer = User(
        id="buyer-order-01",
        name="Chidi Okafor",
        email="chidi.okafor@unijos.edu.ng",
        trust_score=50,
        verification_status="verified",
        wallet_address="0x2222222222222222222222222222222222222222",
    )
    seller = User(
        id="seller-order-01",
        name="Amina Bello",
        email="amina.bello@unijos.edu.ng",
        trust_score=70,
        verification_status="verified",
        wallet_address="0x3333333333333333333333333333333333333333",
    )
    db_session.add(buyer)
    db_session.add(seller)
    db_session.commit()

    listing = MarketplaceListing(
        id="listing-order-01",
        seller_id="seller-order-01",
        title="Laptop Stand",
        description="Aluminum stand",
        category="electronics",
        price=12000.0,
        images=["https://res.cloudinary.com/stand.jpg"],
        status="active",
        inventory_count=2,
    )
    db_session.add(listing)
    db_session.commit()

    order_service = OrderService(db=db_session)
    review_service = ReviewService(db=db_session)

    # 1. Test create_order (creates order + order items)
    created_order = order_service.create_order(
        OrderCreateRequest(
            buyer_id="buyer-order-01",
            listing_id="listing-order-01",
            amount=12000.0,
            quantity=1,
        )
    )
    assert created_order.id is not None
    assert created_order.status == "initiated"
    assert created_order.amount == 12000.0
    assert created_order.listing_title == "Laptop Stand"

    # 2. Handle Blip Pay Webhook (locks escrow)
    locked_order = order_service.handle_webhook(
        payment_reference=created_order.payment_reference,
        blip_status="success",
        raw_payload={"amount": 12000.0, "status": "success"},
    )
    assert locked_order.status == "escrow_locked"
    assert locked_order.escrow_tx_hash is not None
    assert "0xquai_escrow_lock_" in locked_order.escrow_tx_hash

    # 3. Check Idempotency: duplicate webhook calls do not alter escrow or fail
    repeat_order = order_service.handle_webhook(
        payment_reference=created_order.payment_reference,
        blip_status="success",
        raw_payload={"amount": 12000.0, "status": "success"},
    )
    assert repeat_order.status == "escrow_locked"

    # 4. Confirm physical delivery
    delivered_order = order_service.confirm_delivery(
        order_id=created_order.id, actor_id="buyer-order-01"
    )
    assert delivered_order.status == "delivered_pending_release"

    # 5. Release escrow & check automatic Trust Score rewards (+5 Buy, +5 Sell)
    completed_order = order_service.release_escrow(
        order_id=created_order.id, actor_id="buyer-order-01"
    )
    assert completed_order.status == "completed"
    assert completed_order.completed_at is not None

    db_session.refresh(buyer)
    db_session.refresh(seller)
    assert buyer.trust_score == 55  # 50 + 5
    assert seller.trust_score == 75  # 70 + 5

    # 6. Check listing inventory decremented
    db_session.refresh(listing)
    assert listing.inventory_count == 1

    # 7. Submit review and check +2 Trust Score to seller
    review_res = review_service.submit_review(
        ReviewCreateRequest(
            order_id=created_order.id,
            reviewer_id="buyer-order-01",
            reviewee_id="seller-order-01",
            rating=5,
            comment="Excellent laptop stand, delivered quickly!",
        )
    )
    assert review_res.id is not None
    assert review_res.rating == 5

    db_session.refresh(seller)
    assert seller.trust_score == 77  # 75 + 2 review bonus


def test_order_cancellation(db_session):
    buyer = User(id="b-c1", name="Buyer C", email="bc@test.org")
    seller = User(id="s-c1", name="Seller C", email="sc@test.org")
    db_session.add(buyer)
    db_session.add(seller)
    db_session.commit()

    listing = MarketplaceListing(
        id="list-c1",
        seller_id="s-c1",
        title="Test Book",
        description="Book",
        category="books",
        price=1000.0,
        images=["https://res.cloudinary.com/test.jpg"],
        status="active",
        inventory_count=1,
    )
    db_session.add(listing)
    db_session.commit()

    service = OrderService(db=db_session)
    order = service.create_order(
        OrderCreateRequest(buyer_id="b-c1", listing_id="list-c1", amount=1000.0)
    )
    assert order.status == "initiated"

    cancelled = service.cancel_order(order_id=order.id, actor_id="b-c1")
    assert cancelled.status == "cancelled"
