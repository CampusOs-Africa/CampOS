import pytest

from app.core.exceptions import ForbiddenError
from app.models.marketplace import MarketplaceListing
from app.models.order import Order
from app.models.user import User
from app.schemas.escrow import EscrowCreateRequest
from app.services.escrow_service import EscrowService



def test_escrow_service_lifecycle_and_actions(db_session):
    buyer = User(
    id="escrow-buyer-01",
    name="Chidi Okafor",
    email="chidi.esc@unijos.edu.ng",
    verification_status="verified",
    wallet_address="0x2222222222222222222222222222222222222222",
)
    seller = User(
    id="escrow-seller-01",
    name="Amina Bello",
    email="amina.esc@unijos.edu.ng",
    verification_status="verified",
    wallet_address="0x3333333333333333333333333333333333333333",
)
    db_session.add(buyer)
    db_session.add(seller)
    db_session.commit()

    listing = MarketplaceListing(
        id="escrow-listing-01",
        seller_id="escrow-seller-01",
        title="Physics Textbook",
        description="Engineering physics",
        category="books",
        price=4000.0,
        images=["https://res.cloudinary.com/test.jpg"],
        status="active",
        inventory_count=1,
    )
    db_session.add(listing)
    db_session.commit()

    order = Order(
        id="escrow-order-01",
        buyer_id="escrow-buyer-01",
        listing_id="escrow-listing-01",
        seller_id="escrow-seller-01",
        amount=4000.0,
        payment_reference="blip_ref_escrow_01",
        status="initiated",
    )
    db_session.add(order)
    db_session.commit()

    service = EscrowService(db=db_session)

    # 1. Test EscrowRecord creation
    created = service.create_escrow(
        EscrowCreateRequest(
            order_id="escrow-order-01",
            buyer_id="escrow-buyer-01",
            seller_id="escrow-seller-01",
            amount=4000.0,
        )
    )
    assert created.id is not None
    assert created.order_id == "escrow-order-01"
    assert created.state == "CREATED"
    assert created.quai_order_id.startswith("0xquai_escrow_")
    assert created.expires_at is not None

    # 2. Test duplicate creation idempotency
    dup = service.create_escrow(
        EscrowCreateRequest(
            order_id="escrow-order-01",
            buyer_id="escrow-buyer-01",
            seller_id="escrow-seller-01",
            amount=4000.0,
        )
    )
    assert dup.id == created.id

    # 3. Test dispute escrow
    disputed = service.dispute_escrow(
        order_id="escrow-order-01",
        actor_id="escrow-buyer-01",
        reason="Item delayed",
    )
    assert disputed.state == "DISPUTED"

    # 4. Test release escrow (by buyer)
    released = service.release_escrow(
        order_id="escrow-order-01", actor_id="escrow-buyer-01"
    )
    assert released.state == "COMPLETED"
    assert released.escrow_tx_hash is not None
    assert released.escrow_tx_hash.startswith("0xquai_escrow_release_")

    # 5. Verify unauthorized actor cannot release
    with pytest.raises(ForbiddenError):
        service.release_escrow(order_id="escrow-order-01", actor_id="escrow-seller-01")


def test_escrow_service_refund(db_session):
    buyer = User(
    id="eb-02",
    name="Buyer 2",
    email="b2@test.org",
    wallet_address="0x4444444444444444444444444444444444444444",
)

    seller = User(
        id="es-02",
        name="Seller 2",
        email="s2@test.org",
        wallet_address="0x5555555555555555555555555555555555555555",
    )
    db_session.add(buyer)
    db_session.add(seller)
    db_session.commit()

    order = Order(
        id="ord-02",
        buyer_id="eb-02",
        listing_id="fake-listing",
        seller_id="es-02",
        amount=2000.0,
        payment_reference="ref_02",
        status="escrow_locked",
    )
    db_session.add(order)
    db_session.commit()

    service = EscrowService(db=db_session)
    service.create_escrow(
        EscrowCreateRequest(
            order_id="ord-02",
            buyer_id="eb-02",
            seller_id="es-02",
            amount=2000.0,
        )
    )

    refunded = service.refund_escrow(
        order_id="ord-02", actor_id="es-02", reason="Item damaged"
    )
    assert refunded.state == "REFUNDED"
    assert refunded.escrow_tx_hash.startswith("0xquai_escrow_refund_")
