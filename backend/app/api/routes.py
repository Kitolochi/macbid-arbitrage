"""API routes for the MacBid Arbitrage app."""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from app.db import get_db
from app.models.product import Product
from app.models.listing import MacBidListing, AuctionStatus
from app.models.price import PlatformPrice
from app.models.opportunity import Opportunity
from app.models.alert import AlertSetting
from app.api.schemas import (
    OpportunityOut,
    OpportunityDetail,
    ListingOut,
    ListingWithProduct,
    ProductOut,
    PriceOut,
    DashboardStats,
    AlertSettingCreate,
    AlertSettingOut,
)

router = APIRouter()


# --- Opportunities ---

@router.get("/opportunities", response_model=list[OpportunityOut])
async def list_opportunities(
    db: AsyncSession = Depends(get_db),
    sort_by: str = Query("profit", enum=["profit", "roi_pct", "confidence_score", "created_at"]),
    sort_dir: str = Query("desc", enum=["asc", "desc"]),
    platform: Optional[str] = Query(None),
    min_profit: Optional[float] = Query(None),
    min_roi: Optional[float] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    query = select(Opportunity)

    if platform:
        query = query.where(Opportunity.sell_platform == platform)
    if min_profit is not None:
        query = query.where(Opportunity.profit >= min_profit)
    if min_roi is not None:
        query = query.where(Opportunity.roi_pct >= min_roi)

    sort_col = getattr(Opportunity, sort_by)
    query = query.order_by(desc(sort_col) if sort_dir == "desc" else sort_col)
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityDetail)
async def get_opportunity(opportunity_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    product = await db.get(Product, opp.product_id)
    listing = await db.get(MacBidListing, opp.macbid_listing_id)

    prices_result = await db.execute(
        select(PlatformPrice)
        .where(PlatformPrice.product_id == opp.product_id)
        .order_by(PlatformPrice.fetched_at.desc())
    )
    prices = prices_result.scalars().all()

    return OpportunityDetail(
        **{c.name: getattr(opp, c.name) for c in opp.__table__.columns},
        product=product,
        listing=listing,
        platform_prices=prices,
    )


# --- Listings ---

@router.get("/listings", response_model=list[ListingOut])
async def list_listings(
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    query = select(MacBidListing).order_by(MacBidListing.created_at.desc())

    if status:
        query = query.where(MacBidListing.status == status)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# --- Product Prices ---

@router.get("/products/{product_id}/prices", response_model=list[PriceOut])
async def get_product_prices(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlatformPrice)
        .where(PlatformPrice.product_id == product_id)
        .order_by(PlatformPrice.fetched_at.desc())
    )
    return result.scalars().all()


# --- Dashboard Stats ---

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Total opportunities
    total_result = await db.execute(select(func.count(Opportunity.id)))
    total = total_result.scalar() or 0

    # Average profit and ROI
    avg_result = await db.execute(
        select(func.avg(Opportunity.profit), func.avg(Opportunity.roi_pct))
    )
    row = avg_result.one()
    avg_profit = float(row[0] or 0)
    avg_roi = float(row[1] or 0)

    # Active listings count
    active_result = await db.execute(
        select(func.count(MacBidListing.id))
        .where(MacBidListing.status == AuctionStatus.ACTIVE)
    )
    active_listings = active_result.scalar() or 0

    # Top categories (from products linked to opportunities)
    cat_query = (
        select(Product.category, func.count(Opportunity.id).label("count"))
        .join(Opportunity, Opportunity.product_id == Product.id)
        .where(Product.category.isnot(None))
        .group_by(Product.category)
        .order_by(desc("count"))
        .limit(5)
    )
    cat_result = await db.execute(cat_query)
    top_categories = [{"category": r[0], "count": r[1]} for r in cat_result.all()]

    # Recent opportunities
    recent_result = await db.execute(
        select(Opportunity)
        .order_by(Opportunity.created_at.desc())
        .limit(10)
    )
    recent = recent_result.scalars().all()

    return DashboardStats(
        total_opportunities=total,
        avg_profit=round(avg_profit, 2),
        avg_roi=round(avg_roi, 2),
        top_categories=top_categories,
        active_listings=active_listings,
        recent_opportunities=recent,
    )


# --- SSE Stream ---

@router.get("/stream")
async def stream_opportunities(db: AsyncSession = Depends(get_db)):
    """Server-Sent Events endpoint for real-time opportunity updates."""

    async def event_generator():
        last_check = datetime.now(timezone.utc)
        while True:
            await asyncio.sleep(10)  # Check every 10 seconds
            result = await db.execute(
                select(Opportunity)
                .where(Opportunity.created_at > last_check)
                .order_by(Opportunity.created_at.desc())
                .limit(20)
            )
            new_opps = result.scalars().all()
            last_check = datetime.now(timezone.utc)

            for opp in new_opps:
                data = {
                    "id": str(opp.id),
                    "product_id": str(opp.product_id),
                    "profit": float(opp.profit),
                    "roi_pct": float(opp.roi_pct),
                    "sell_platform": opp.sell_platform,
                    "buy_cost": float(opp.buy_cost),
                    "estimated_sell_price": float(opp.estimated_sell_price),
                }
                yield {"event": "new_opportunity", "data": json.dumps(data)}

    return EventSourceResponse(event_generator())


# --- Alert Settings ---

@router.post("/alerts/settings", response_model=AlertSettingOut)
async def create_alert_setting(body: AlertSettingCreate, db: AsyncSession = Depends(get_db)):
    setting = AlertSetting(
        id=uuid.uuid4(),
        email=body.email,
        min_profit=body.min_profit,
        min_roi=body.min_roi,
        watched_categories=body.watched_categories,
        is_active=body.is_active,
    )
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return setting


@router.get("/alerts/settings", response_model=list[AlertSettingOut])
async def list_alert_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertSetting).order_by(AlertSetting.created_at.desc()))
    return result.scalars().all()


@router.put("/alerts/settings/{setting_id}", response_model=AlertSettingOut)
async def update_alert_setting(
    setting_id: uuid.UUID,
    body: AlertSettingCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AlertSetting).where(AlertSetting.id == setting_id))
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail="Alert setting not found")

    setting.email = body.email
    setting.min_profit = body.min_profit
    setting.min_roi = body.min_roi
    setting.watched_categories = body.watched_categories
    setting.is_active = body.is_active
    await db.commit()
    await db.refresh(setting)
    return setting
