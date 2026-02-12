"""Celery tasks for looking up prices on eBay and Amazon."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.celery_config import celery_app
from app.config import get_settings
from app.integrations.ebay import EbayClient
from app.integrations.keepa import KeepaClient
from app.models.product import Product
from app.models.price import PlatformPrice, Platform

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_async_session():
    engine = create_async_engine(settings.database_url)
    return async_sessionmaker(engine, expire_on_commit=False)


async def _lookup_ebay(product_id: str, upc: str | None, title: str):
    ebay = EbayClient()
    try:
        results = []
        if upc:
            results = await ebay.search_by_upc(upc)
        if not results and title:
            # Fall back to keyword search
            results = await ebay.search_by_keyword(title)

        if not results:
            return

        Session = _get_async_session()
        async with Session() as db:
            for item in results:
                price = PlatformPrice(
                    id=uuid.uuid4(),
                    product_id=uuid.UUID(product_id),
                    platform=Platform.EBAY,
                    price=item["price"],
                    condition=item.get("condition"),
                    shipping_cost=item.get("shipping_cost", 0),
                    url=item.get("url"),
                    seller_info=item.get("seller"),
                    extra_data=item.get("extra_data"),
                    fetched_at=datetime.now(timezone.utc),
                )
                db.add(price)
            await db.commit()
            logger.info("Stored %d eBay prices for product %s", len(results), product_id)
    finally:
        await ebay.close()


async def _lookup_keepa(product_id: str, upc: str | None):
    if not settings.keepa_api_key:
        logger.debug("Keepa API key not configured, skipping")
        return

    keepa = KeepaClient()
    try:
        result = None
        if upc:
            result = await keepa.lookup_by_upc(upc)

        if not result:
            return

        Session = _get_async_session()
        async with Session() as db:
            # Update product with ASIN if we found it
            if result.get("asin"):
                prod_result = await db.execute(
                    select(Product).where(Product.id == uuid.UUID(product_id))
                )
                product = prod_result.scalar_one_or_none()
                if product and not product.asin:
                    product.asin = result["asin"]

            # Store the price
            if result.get("price") is not None:
                price = PlatformPrice(
                    id=uuid.uuid4(),
                    product_id=uuid.UUID(product_id),
                    platform=Platform.AMAZON,
                    price=result["price"],
                    condition="new",
                    shipping_cost=0,  # Amazon typically free shipping
                    url=result.get("url"),
                    extra_data={
                        "asin": result.get("asin"),
                        "bsr": result.get("bsr"),
                        "avg_price_30d": result.get("avg_price_30d"),
                        "avg_price_90d": result.get("avg_price_90d"),
                        "new_offer_count": result.get("new_offer_count"),
                        "used_offer_count": result.get("used_offer_count"),
                        "fba_fees": result.get("fba_fees"),
                    },
                    fetched_at=datetime.now(timezone.utc),
                )
                db.add(price)

            await db.commit()
            logger.info("Stored Keepa/Amazon price for product %s", product_id)
    finally:
        await keepa.close()


@celery_app.task(name="app.tasks.lookup.lookup_prices", bind=True, max_retries=2)
def lookup_prices(self, product_id: str, upc: str | None, title: str):
    """Look up prices on eBay and Amazon for a product."""
    try:
        asyncio.run(asyncio.gather(
            _lookup_ebay(product_id, upc, title),
            _lookup_keepa(product_id, upc),
        ))
    except Exception as exc:
        logger.exception("Price lookup failed for product %s", product_id)
        self.retry(exc=exc, countdown=120)
