"""Opportunity engine: compares MacBid listings against platform prices to find arbitrage."""

import logging
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import MacBidListing, AuctionStatus
from app.models.price import PlatformPrice
from app.models.opportunity import Opportunity
from app.services.calculator import calculate_profit

logger = logging.getLogger(__name__)


def compute_confidence_score(
    price_count: int,
    freshness_hours: float,
    bsr: int | None = None,
) -> float:
    """Score 0-100 indicating how reliable the opportunity estimate is.

    Factors:
    - Number of comparable prices found (more = better)
    - How recent the price data is (fresher = better)
    - BSR rank for Amazon (lower = better selling)
    """
    score = 0.0

    # Price data quantity (up to 40 points)
    if price_count >= 10:
        score += 40
    elif price_count >= 5:
        score += 30
    elif price_count >= 3:
        score += 20
    elif price_count >= 1:
        score += 10

    # Freshness (up to 30 points)
    if freshness_hours <= 2:
        score += 30
    elif freshness_hours <= 6:
        score += 25
    elif freshness_hours <= 12:
        score += 20
    elif freshness_hours <= 24:
        score += 10
    else:
        score += 5

    # BSR (up to 30 points) - lower BSR = better
    if bsr is not None:
        if bsr <= 5000:
            score += 30
        elif bsr <= 20000:
            score += 25
        elif bsr <= 50000:
            score += 20
        elif bsr <= 100000:
            score += 15
        elif bsr <= 500000:
            score += 10
        else:
            score += 5
    else:
        score += 15  # neutral when no BSR data

    return min(score, 100)


async def compute_opportunities_for_listing(
    db: AsyncSession,
    listing: MacBidListing,
) -> list[Opportunity]:
    """Compute arbitrage opportunities for a single MacBid listing."""
    product_id = listing.product_id
    now = datetime.now(timezone.utc)

    # Get all platform prices for this product
    result = await db.execute(
        select(PlatformPrice)
        .where(PlatformPrice.product_id == product_id)
        .where(PlatformPrice.fetched_at >= now - timedelta(hours=48))
        .order_by(PlatformPrice.fetched_at.desc())
    )
    prices = result.scalars().all()

    if not prices:
        return []

    # Group prices by platform
    platform_prices: dict[str, list[PlatformPrice]] = {}
    for p in prices:
        platform_prices.setdefault(p.platform.value, []).append(p)

    opportunities = []

    for platform, price_list in platform_prices.items():
        # Use median price as the estimated sell price for robustness
        sorted_prices = sorted(price_list, key=lambda x: float(x.price))
        mid = len(sorted_prices) // 2
        median_price = float(sorted_prices[mid].price)

        # Average shipping cost
        avg_shipping = sum(float(p.shipping_cost) for p in price_list) / len(price_list)

        # Get freshness
        newest = max(p.fetched_at for p in price_list)
        freshness_hours = (now - newest).total_seconds() / 3600

        # Get BSR if available (from extra_data on Amazon prices)
        bsr = None
        if platform == "amazon":
            for p in price_list:
                if p.extra_data and p.extra_data.get("bsr"):
                    bsr = p.extra_data["bsr"]
                    break

        # Calculate profit
        result = calculate_profit(
            winning_bid=float(listing.current_bid),
            sell_price=median_price,
            platform=platform,
            shipping_cost=round(avg_shipping, 2),
        )

        confidence = compute_confidence_score(
            price_count=len(price_list),
            freshness_hours=freshness_hours,
            bsr=bsr,
        )

        opp = Opportunity(
            id=uuid.uuid4(),
            product_id=product_id,
            macbid_listing_id=listing.id,
            buy_cost=result.cost.total_cost,
            estimated_sell_price=median_price,
            sell_platform=platform,
            platform_fees=result.revenue.platform_fees,
            shipping_cost=result.revenue.shipping_cost,
            profit=result.profit,
            roi_pct=result.roi_pct,
            confidence_score=confidence,
        )
        opportunities.append(opp)

    return opportunities


async def refresh_all_opportunities(db: AsyncSession) -> int:
    """Recompute opportunities for all active MacBid listings."""
    result = await db.execute(
        select(MacBidListing).where(MacBidListing.status == AuctionStatus.ACTIVE)
    )
    listings = result.scalars().all()

    count = 0
    for listing in listings:
        # Delete stale opportunities for this listing
        old = await db.execute(
            select(Opportunity).where(Opportunity.macbid_listing_id == listing.id)
        )
        for opp in old.scalars().all():
            await db.delete(opp)

        new_opps = await compute_opportunities_for_listing(db, listing)
        for opp in new_opps:
            db.add(opp)
            count += 1

    await db.commit()
    logger.info("Refreshed %d opportunities across %d listings", count, len(listings))
    return count
