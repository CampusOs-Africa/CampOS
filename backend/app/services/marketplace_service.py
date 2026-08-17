from sqlalchemy.orm import Session

from app.core.cache import cache_get, cache_set, invalidate_marketplace_cache
from app.core.exceptions import EntityNotFoundError, ForbiddenError
from app.models.marketplace import MarketplaceListing
from app.models.user import User
from app.repositories.marketplace_repository import MarketplaceRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_repository import UserRepository
from app.schemas.marketplace import (
    MarketplaceCategoryResponse,
    MarketplaceListingCreate,
    MarketplaceListingResponse,
    MarketplaceListingUpdate,
    SellerProfileResponse,
)


class MarketplaceService:
    def __init__(self, db: Session):
        self.db = db
        self.listing_repo = MarketplaceRepository(db)
        self.user_repo = UserRepository(db)
        self.order_repo = OrderRepository(db)
        self.review_repo = ReviewRepository(db)

    def _enrich_listings(
        self, listings: list[MarketplaceListing]
    ) -> list[MarketplaceListingResponse]:
        if not listings:
            return []
        seller_ids = list({l.seller_id for l in listings})
        sellers = self.db.query(User).filter(User.id.in_(seller_ids)).all()
        seller_map = {u.id: u for u in sellers}

        res_list = []
        for listing in listings:
            res = MarketplaceListingResponse.model_validate(listing)
            seller = seller_map.get(listing.seller_id)
            if seller:
                res.seller_name = seller.name
                res.seller_trust_score = seller.trust_score
                res.seller_verified = seller.verification_status in (
                    "verified",
                    "approved",
                )
            res_list.append(res)
        return res_list

    def _enrich_listing(
        self, listing: MarketplaceListing
    ) -> MarketplaceListingResponse:
        return self._enrich_listings([listing])[0]

    def get_categories(self) -> list[MarketplaceCategoryResponse]:
        cache_key = "campusos:cache:marketplace:categories"
        cached = cache_get(cache_key)
        if cached:
            return [
                MarketplaceCategoryResponse.model_validate(c) for c in cached
            ]

        cats = self.listing_repo.get_all_categories()
        counts = self.listing_repo.get_category_counts()
        res = []
        for c in cats:
            c.active_count = counts.get(c.id, 0)
            res.append(MarketplaceCategoryResponse.model_validate(c))

        cache_set(
            cache_key,
            [c.model_dump(mode="json") for c in res],
            ttl_seconds=60,
        )
        return res

    def create_listing(
        self, req: MarketplaceListingCreate
    ) -> MarketplaceListingResponse:
        seller = self.user_repo.get_by_id(req.seller_id)
        if not seller:
            raise EntityNotFoundError("User", req.seller_id)

        if seller.verification_status not in ("verified", "approved"):
            raise ForbiddenError(
                "You must possess an approved Verified Student Identity to list items for sale on CampusOS."
            )

        # Phase 1: Require seller has a connected wallet (canonical blockchain identity)
        if not seller.wallet_address:
            raise ForbiddenError(
                "You must connect a Quai EVM wallet before creating marketplace listings. "
                "This ensures your blockchain identity is established for escrow transactions."
            )

        listing = MarketplaceListing(
            seller_id=req.seller_id,
            title=req.title,
            description=req.description,
            category=req.category.lower(),
            price=req.price,
            condition=req.condition.lower(),
            inventory_count=req.inventory_count,
            images=req.images,
            status="active",
        )
        created = self.listing_repo.create(listing)
        invalidate_marketplace_cache()
        return self._enrich_listing(created)

    def get_listing_by_id(self, listing_id: str) -> MarketplaceListingResponse:
        listing = self.listing_repo.get_by_id(listing_id)
        if not listing:
            raise EntityNotFoundError("MarketplaceListing", listing_id)
        return self._enrich_listing(listing)

    def get_catalog(
        self,
        category: str | None = None,
        condition: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        search: str | None = None,
        seller_id: str | None = None,
        status: str | None = "active",
        skip: int = 0,
        limit: int = 20,
    ) -> list[MarketplaceListingResponse]:
        cache_key = f"campusos:cache:marketplace:catalog:{category}:{condition}:{min_price}:{max_price}:{search}:{seller_id}:{status}:{skip}:{limit}"
        cached = cache_get(cache_key)
        if cached:
            return [
                MarketplaceListingResponse.model_validate(item)
                for item in cached
            ]

        listings = self.listing_repo.get_catalog(
            category=category,
            condition=condition,
            min_price=min_price,
            max_price=max_price,
            search=search,
            seller_id=seller_id,
            status=status,
            skip=skip,
            limit=limit,
        )
        res = self._enrich_listings(listings)
        cache_set(
            cache_key,
            [r.model_dump(mode="json") for r in res],
            ttl_seconds=30,
        )
        return res

    def update_listing(
        self,
        listing_id: str,
        actor_id: str,
        req: MarketplaceListingUpdate,
    ) -> MarketplaceListingResponse:
        listing = self.listing_repo.get_by_id(listing_id)
        if not listing:
            raise EntityNotFoundError("MarketplaceListing", listing_id)

        actor = self.user_repo.get_by_id(actor_id)
        if listing.seller_id != actor_id and (not actor or actor.role != "admin"):
            raise ForbiddenError(
                "Only the listing seller or an administrator can update this listing."
            )

        if req.title is not None:
            listing.title = req.title
        if req.description is not None:
            listing.description = req.description
        if req.category is not None:
            listing.category = req.category.lower()
        if req.price is not None:
            listing.price = req.price
        if req.condition is not None:
            listing.condition = req.condition.lower()
        if req.inventory_count is not None:
            listing.inventory_count = req.inventory_count
            if listing.inventory_count == 0:
                listing.status = "sold"
            elif listing.status == "sold" and listing.inventory_count > 0:
                listing.status = "active"
        if req.images is not None:
            listing.images = req.images
        if req.status is not None:
            listing.status = req.status

        updated = self.listing_repo.update(listing)
        invalidate_marketplace_cache()
        return self._enrich_listing(updated)

    def delete_listing(self, listing_id: str, actor_id: str) -> bool:
        listing = self.listing_repo.get_by_id(listing_id)
        if not listing:
            raise EntityNotFoundError("MarketplaceListing", listing_id)

        actor = self.user_repo.get_by_id(actor_id)
        if listing.seller_id != actor_id and (not actor or actor.role != "admin"):
            raise ForbiddenError(
                "Only the listing seller or an administrator can delete this listing."
            )

        success = self.listing_repo.delete(listing_id)
        if success:
            invalidate_marketplace_cache()
        return success

    def get_seller_profile(self, seller_id: str) -> SellerProfileResponse:
        seller = self.user_repo.get_by_id(seller_id)
        if not seller:
            raise EntityNotFoundError("User", seller_id)

        active_count = self.listing_repo.count_by_seller(
            seller_id=seller_id, status="active"
        )
        completed_count = self.order_repo.count_by_seller(
            seller_id=seller_id, status="completed"
        )
        avg_rating, _ = self.review_repo.get_average_rating(seller_id)
        reviews = self.review_repo.get_by_reviewee(seller_id, skip=0, limit=10)

        return SellerProfileResponse(
            user_id=seller.id,
            name=seller.name,
            email=seller.email,
            trust_score=seller.trust_score,
            is_verified=seller.verification_status in ("verified", "approved"),
            active_listings_count=active_count,
            total_sales_count=completed_count,
            average_rating=avg_rating,
            reviews=reviews,
        )
