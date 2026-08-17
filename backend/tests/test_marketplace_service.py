import pytest

from app.core.exceptions import ForbiddenError
from app.models.user import User
from app.schemas.marketplace import MarketplaceListingCreate, MarketplaceListingUpdate
from app.services.marketplace_service import MarketplaceService


def test_marketplace_listing_creation_and_catalog(db_session):
    verified_seller = User(
        id="seller-verified-01",
        name="Amina Bello",
        email="amina.bello@unijos.edu.ng",
        role="student",
        verification_status="verified",
        trust_score=75,
    )
    unverified_student = User(
        id="student-unverified-01",
        name="Chidi Okafor",
        email="chidi.okafor@unijos.edu.ng",
        role="student",
        verification_status="pending",
        trust_score=50,
    )
    db_session.add(verified_seller)
    db_session.add(unverified_student)
    db_session.commit()

    service = MarketplaceService(db=db_session)

    # 1. Unverified student cannot create listing (RBAC gate enforcement)
    with pytest.raises(ForbiddenError) as exc_info:
        service.create_listing(
            MarketplaceListingCreate(
                seller_id="student-unverified-01",
                title="Calculus Textbook",
                description="Engineering calculus volume 1",
                category="books",
                price=4500.0,
                images=["https://res.cloudinary.com/test/book.jpg"],
            )
        )
    assert "must possess an approved Verified Student Identity" in str(exc_info.value)

    # 2. Verified student can create listing
    listing = service.create_listing(
        MarketplaceListingCreate(
            seller_id="seller-verified-01",
            title="Calculus Textbook",
            description="Engineering calculus volume 1 in great condition",
            category="books",
            price=4500.0,
            condition="good",
            inventory_count=2,
            images=["https://res.cloudinary.com/test/book.jpg"],
        )
    )
    assert listing.id is not None
    assert listing.seller_id == "seller-verified-01"
    assert listing.title == "Calculus Textbook"
    assert listing.price == 4500.0
    assert listing.seller_name == "Amina Bello"
    assert listing.seller_verified is True

    # 3. Test catalog search and filtering
    catalog = service.get_catalog(category="books")
    assert len(catalog) == 1
    assert catalog[0].id == listing.id

    search_res = service.get_catalog(search="calculus")
    assert len(search_res) == 1

    empty_res = service.get_catalog(category="electronics")
    assert len(empty_res) == 0

    # 4. Test updating listing
    updated = service.update_listing(
        listing_id=listing.id,
        actor_id="seller-verified-01",
        req=MarketplaceListingUpdate(price=4000.0, title="Calculus Textbook (Discounted)"),
    )
    assert updated.price == 4000.0
    assert updated.title == "Calculus Textbook (Discounted)"

    # 5. Test seller profile composite query
    profile = service.get_seller_profile("seller-verified-01")
    assert profile.user_id == "seller-verified-01"
    assert profile.active_listings_count == 1
    assert profile.trust_score == 75
