"""Pydantic schemas for API request/response models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


# --- Products ---

class ProductOut(BaseModel):
    id: UUID
    upc: str | None
    asin: str | None
    title: str
    category: str | None
    image_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- MacBid Listings ---

class ListingOut(BaseModel):
    id: UUID
    listing_id: str
    product_id: UUID
    current_bid: float
    retail_price: float | None
    condition: str
    warehouse_location: str | None
    closes_at: datetime | None
    status: str
    url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ListingWithProduct(ListingOut):
    product: ProductOut


# --- Platform Prices ---

class PriceOut(BaseModel):
    id: UUID
    platform: str
    price: float
    condition: str | None
    shipping_cost: float
    url: str | None
    seller_info: str | None
    fetched_at: datetime

    model_config = {"from_attributes": True}


# --- Opportunities ---

class OpportunityOut(BaseModel):
    id: UUID
    product_id: UUID
    macbid_listing_id: UUID
    buy_cost: float
    estimated_sell_price: float
    sell_platform: str
    platform_fees: float
    shipping_cost: float
    profit: float
    roi_pct: float
    confidence_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class OpportunityDetail(OpportunityOut):
    product: ProductOut
    listing: ListingOut
    platform_prices: list[PriceOut]


# --- Dashboard Stats ---

class DashboardStats(BaseModel):
    total_opportunities: int
    avg_profit: float
    avg_roi: float
    top_categories: list[dict]
    active_listings: int
    recent_opportunities: list[OpportunityOut]


# --- Alert Settings ---

class AlertSettingCreate(BaseModel):
    email: str
    min_profit: float = 10.0
    min_roi: float = 20.0
    watched_categories: list[str] | None = None
    is_active: bool = True


class AlertSettingOut(BaseModel):
    id: UUID
    email: str
    min_profit: float
    min_roi: float
    watched_categories: list[str] | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
