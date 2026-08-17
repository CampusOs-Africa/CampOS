from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.marketplace import MarketplaceCategory, MarketplaceListing


class MarketplaceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, listing: MarketplaceListing) -> MarketplaceListing:
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def get_by_id(self, listing_id: str) -> MarketplaceListing | None:
        return (
            self.db.query(MarketplaceListing)
            .filter(MarketplaceListing.id == listing_id)
            .first()
        )

    def update(self, listing: MarketplaceListing) -> MarketplaceListing:
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def delete(self, listing_id: str) -> bool:
        listing = self.get_by_id(listing_id)
        if not listing:
            return False
        self.db.delete(listing)
        self.db.commit()
        return True

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
    ) -> list[MarketplaceListing]:
        query = self.db.query(MarketplaceListing)

        if status:
            query = query.filter(MarketplaceListing.status == status)
        if category and category.lower() != "all":
            query = query.filter(MarketplaceListing.category == category.lower())
        if condition and condition.lower() != "all":
            query = query.filter(MarketplaceListing.condition == condition.lower())
        if min_price is not None:
            query = query.filter(MarketplaceListing.price >= min_price)
        if max_price is not None:
            query = query.filter(MarketplaceListing.price <= max_price)
        if seller_id:
            query = query.filter(MarketplaceListing.seller_id == seller_id)
        if search:
            clean_search = search.strip()
            query = query.filter(
                or_(
                    MarketplaceListing.title.ilike(f"%{clean_search}%"),
                    MarketplaceListing.description.ilike(f"%{clean_search}%"),
                )
            )

        return (
            query.order_by(MarketplaceListing.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_category_counts(self) -> dict[str, int]:
        rows = (
            self.db.query(
                MarketplaceListing.category, func.count(MarketplaceListing.id)
            )
            .filter(MarketplaceListing.status == "active")
            .group_by(MarketplaceListing.category)
            .all()
        )
        return {cat: int(cnt) for cat, cnt in rows}

    def count_by_seller(self, seller_id: str, status: str = "active") -> int:
        return (
            self.db.query(func.count(MarketplaceListing.id))
            .filter(
                MarketplaceListing.seller_id == seller_id,
                MarketplaceListing.status == status,
            )
            .scalar()
            or 0
        )

    def get_all_categories(self) -> list[MarketplaceCategory]:
        cats = (
            self.db.query(MarketplaceCategory)
            .order_by(MarketplaceCategory.name.asc())
            .all()
        )
        if not cats:
            defaults = [
                MarketplaceCategory(
                    id="books",
                    name="Books & Notes",
                    description="Textbooks & past questions",
                    icon="BookOpen",
                ),
                MarketplaceCategory(
                    id="electronics",
                    name="Electronics",
                    description="Laptops, phones & gadgets",
                    icon="Laptop",
                ),
                MarketplaceCategory(
                    id="accommodation",
                    name="Housing",
                    description="Hostels & room shares",
                    icon="Home",
                ),
                MarketplaceCategory(
                    id="tutoring",
                    name="Tutoring",
                    description="Academic coaching & lessons",
                    icon="GraduationCap",
                ),
                MarketplaceCategory(
                    id="tickets",
                    name="Event Tickets",
                    description="Campus shows & NFT passes",
                    icon="Ticket",
                ),
                MarketplaceCategory(
                    id="services",
                    name="Services",
                    description="Laundry, repairs & design",
                    icon="Wrench",
                ),
            ]
            for c in defaults:
                self.db.add(c)
            self.db.commit()
            cats = (
                self.db.query(MarketplaceCategory)
                .order_by(MarketplaceCategory.name.asc())
                .all()
            )
        return cats

    def get_category_by_id(self, cat_id: str) -> MarketplaceCategory | None:
        return (
            self.db.query(MarketplaceCategory)
            .filter(MarketplaceCategory.id == cat_id)
            .first()
        )

    def create_category(self, cat: MarketplaceCategory) -> MarketplaceCategory:
        self.db.add(cat)
        self.db.commit()
        self.db.refresh(cat)
        return cat
