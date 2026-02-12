"""Celery tasks for scraping MacBid listings."""

import asyncio
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.celery_config import celery_app
from app.config import get_settings
from app.scrapers.macbid import MacBidScraper
from app.models.product import Product
from app.models.listing import MacBidListing, AuctionStatus, ItemCondition

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_async_session():
    engine = create_async_engine(settings.database_url)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _run_scrape():
    scraper = MacBidScraper()
    items = await scraper.run()

    Session = _get_async_session()
    async with Session() as db:
        new_listings = 0
        updated_listings = 0

        for item in items:
            listing_id = item["listing_id"]

            # Check if listing already exists
            result = await db.execute(
                select(MacBidListing).where(MacBidListing.listing_id == listing_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update bid price
                existing.current_bid = item["current_bid"]
                if item.get("closes_at"):
                    existing.closes_at = item["closes_at"]
                updated_listings += 1
                continue

            # Find or create product
            product = None
            if item.get("upc"):
                result = await db.execute(
                    select(Product).where(Product.upc == item["upc"])
                )
                product = result.scalar_one_or_none()

            if not product:
                product = Product(
                    id=uuid.uuid4(),
                    upc=item.get("upc"),
                    title=item["title"],
                    image_url=item.get("image_url"),
                )
                db.add(product)
                await db.flush()

            # Create listing
            condition_str = item.get("condition", "unknown")
            try:
                condition = ItemCondition(condition_str)
            except ValueError:
                condition = ItemCondition.UNKNOWN

            listing = MacBidListing(
                id=uuid.uuid4(),
                listing_id=listing_id,
                product_id=product.id,
                current_bid=item["current_bid"] or 0,
                retail_price=item.get("retail_price"),
                condition=condition,
                warehouse_location=item.get("warehouse_location"),
                closes_at=item.get("closes_at"),
                status=AuctionStatus.ACTIVE,
                url=item.get("url"),
                extra_data=item.get("extra_data"),
            )
            db.add(listing)
            new_listings += 1

            # Trigger price lookups for new listings
            from app.tasks.lookup import lookup_prices
            lookup_prices.delay(str(product.id), item.get("upc"), item["title"])

        await db.commit()
        logger.info("Scrape complete: %d new, %d updated", new_listings, updated_listings)


@celery_app.task(name="app.tasks.scrape.scrape_macbid", bind=True, max_retries=3)
def scrape_macbid(self):
    """Scrape MacBid auctions and store new/updated listings."""
    try:
        asyncio.run(_run_scrape())
    except Exception as exc:
        logger.exception("MacBid scrape failed")
        self.retry(exc=exc, countdown=60)
