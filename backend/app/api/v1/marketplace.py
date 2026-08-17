from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_strict
from app.models.user import User
from app.schemas.marketplace import (
    MarketplaceCategoryResponse,
    MarketplaceListingCreate,
    MarketplaceListingResponse,
    MarketplaceListingUpdate,
    SellerProfileResponse,
)
from app.services.marketplace_service import MarketplaceService

router = APIRouter(prefix="/marketplace", tags=["Campus Marketplace"])


def get_marketplace_service(db: Session = Depends(get_db)) -> MarketplaceService:
    return MarketplaceService(db=db)


@router.get(
    "/categories",
    response_model=list[MarketplaceCategoryResponse],
    summary="List all marketplace categories",
    description="Returns list of available marketplace categories with active listing counts.",
)
def get_marketplace_categories(
    response: Response,
    service: MarketplaceService = Depends(get_marketplace_service),
):
    response.headers["Cache-Control"] = (
        "public, max-age=30, stale-while-revalidate=60"
    )
    return service.get_categories()


@router.get(
    "",
    response_model=list[MarketplaceListingResponse],
    summary="Get filterable marketplace catalog",
    description="Returns active marketplace listings filterable by category, condition, price range, and search keyword.",
)
@router.get(
    "/",
    response_model=list[MarketplaceListingResponse],
    summary="Get filterable marketplace catalog",
    description="Returns active marketplace listings filterable by category, condition, price range, and search keyword.",
)
@router.get(
    "/listings",
    response_model=list[MarketplaceListingResponse],
    summary="Get filterable marketplace catalog",
    description="Returns active marketplace listings filterable by category, condition, price range, and search keyword.",
)
def get_marketplace_catalog(
    response: Response,
    category: str
    | None = Query(
        None, description="books|electronics|accommodation|tutoring|tickets|services"
    ),
    condition: str | None = Query(None, description="new|like_new|good|fair|poor"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    search: str | None = Query(None, description="Search title and description"),
    seller_id: str | None = Query(None, description="Filter by seller UUID"),
    status: str
    | None = Query("active", description="Filter by status ('active', 'sold', etc.)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    response.headers["Cache-Control"] = (
        "public, max-age=15, stale-while-revalidate=30"
    )
    return service.get_catalog(
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


@router.post(
    "",
    response_model=MarketplaceListingResponse,
    status_code=201,
    summary="Create a marketplace listing",
    description="Creates a new listing. Enforces RBAC gate: seller must possess an approved Verified Student Identity.",
)
@router.post(
    "/",
    response_model=MarketplaceListingResponse,
    status_code=201,
    summary="Create a marketplace listing",
    description="Creates a new listing. Enforces RBAC gate: seller must possess an approved Verified Student Identity.",
)
@router.post(
    "/listings",
    response_model=MarketplaceListingResponse,
    status_code=201,
    summary="Create a marketplace listing",
    description="Creates a new listing. Enforces RBAC gate: seller must possess an approved Verified Student Identity.",
)
def create_listing(
    body: MarketplaceListingCreate,
    service: MarketplaceService = Depends(get_marketplace_service),
    current_user: User = Depends(get_current_user_strict),
):
    # The authenticated JWT is the sole source of truth for seller identity.
    # A client-supplied seller_id cannot impersonate another account.
    if body.seller_id is not None and body.seller_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create listings under your own account.",
        )
    body.seller_id = current_user.id
    return service.create_listing(body)


@router.get(
    "/sellers/{seller_id}",
    response_model=SellerProfileResponse,
    summary="Get seller reputation profile",
    description="Returns seller user profile, Trust Score, active listings count, total sales, and peer reviews.",
)
def get_seller_profile(
    seller_id: str,
    service: MarketplaceService = Depends(get_marketplace_service),
):
    return service.get_seller_profile(seller_id)


@router.get(
    "/{listing_id}",
    response_model=MarketplaceListingResponse,
    summary="Get listing by ID",
    description="Returns detailed marketplace listing enriched with seller profile and trust badge.",
)
@router.get(
    "/listings/{listing_id}",
    response_model=MarketplaceListingResponse,
    summary="Get listing by ID",
    description="Returns detailed marketplace listing enriched with seller profile and trust badge.",
)
def get_listing_by_id(
    listing_id: str,
    service: MarketplaceService = Depends(get_marketplace_service),
):
    return service.get_listing_by_id(listing_id)


@router.put(
    "/{listing_id}",
    response_model=MarketplaceListingResponse,
    summary="Update marketplace listing",
    description="Updates listing attributes. Enforces ownership check (seller or admin only).",
)
@router.put(
    "/listings/{listing_id}",
    response_model=MarketplaceListingResponse,
    summary="Update marketplace listing",
    description="Updates listing attributes. Enforces ownership check (seller or admin only).",
)
def update_listing(
    listing_id: str,
    body: MarketplaceListingUpdate,
    service: MarketplaceService = Depends(get_marketplace_service),
    current_user: User = Depends(get_current_user_strict),
):
    return service.update_listing(
        listing_id=listing_id, actor_id=current_user.id, req=body
    )


@router.delete(
    "/{listing_id}",
    summary="Delete marketplace listing",
    description="Deletes or suspends listing. Enforces ownership check.",
)
@router.delete(
    "/listings/{listing_id}",
    summary="Delete marketplace listing",
    description="Deletes or suspends listing. Enforces ownership check.",
)
def delete_listing(
    listing_id: str,
    service: MarketplaceService = Depends(get_marketplace_service),
    current_user: User = Depends(get_current_user_strict),
):
    success = service.delete_listing(
        listing_id=listing_id, actor_id=current_user.id
    )
    return {"success": success, "listing_id": listing_id}
