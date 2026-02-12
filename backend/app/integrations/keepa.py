import logging
import json

import httpx
import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

KEEPA_API_BASE = "https://api.keepa.com"
CACHE_TTL = 14400  # 4 hours


class KeepaClient:
    """Keepa API client for Amazon price history and product data."""

    def __init__(self):
        self._http = httpx.AsyncClient(timeout=20)
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def lookup_by_upc(self, upc: str) -> dict | None:
        """Look up an Amazon product by UPC via Keepa."""
        cache_key = f"keepa:upc:{upc}"
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        resp = await self._http.get(
            f"{KEEPA_API_BASE}/product",
            params={
                "key": settings.keepa_api_key,
                "domain": "1",  # Amazon.com (US)
                "code": upc,
                "stats": "180",  # 180-day stats
                "offers": "20",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        products = data.get("products", [])
        if not products:
            return None

        result = self._parse_product(products[0])
        await self._set_cached(cache_key, result)
        return result

    async def lookup_by_asin(self, asin: str) -> dict | None:
        """Look up an Amazon product by ASIN via Keepa."""
        cache_key = f"keepa:asin:{asin}"
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        resp = await self._http.get(
            f"{KEEPA_API_BASE}/product",
            params={
                "key": settings.keepa_api_key,
                "domain": "1",
                "asin": asin,
                "stats": "180",
                "offers": "20",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        products = data.get("products", [])
        if not products:
            return None

        result = self._parse_product(products[0])
        await self._set_cached(cache_key, result)
        return result

    def _parse_product(self, product: dict) -> dict:
        """Parse Keepa product data into our standard format."""
        stats = product.get("stats", {})

        # Keepa stores prices in cents (divide by 100)
        def cents_to_dollars(val):
            if val is None or val < 0:
                return None
            return val / 100

        current_prices = stats.get("current", [])
        # Index 0 = Amazon price, 1 = New 3rd party, 2 = Used
        amazon_price = cents_to_dollars(current_prices[0]) if len(current_prices) > 0 else None
        new_3p_price = cents_to_dollars(current_prices[1]) if len(current_prices) > 1 else None
        used_price = cents_to_dollars(current_prices[2]) if len(current_prices) > 2 else None

        # Average prices
        avg_prices = stats.get("avg", [])
        avg_30 = avg_prices[0] if len(avg_prices) > 0 else None
        avg_90 = avg_prices[1] if len(avg_prices) > 1 else None

        # Best Seller Rank
        bsr = None
        sales_ranks = product.get("salesRanks", {})
        if sales_ranks:
            # Get the first category's current BSR
            for _cat_id, ranks in sales_ranks.items():
                if ranks:
                    bsr = ranks[-1] if isinstance(ranks, list) else ranks
                break

        # Offer count
        offer_counts = stats.get("offerCounts", [])
        new_offer_count = offer_counts[0] if len(offer_counts) > 0 else 0
        used_offer_count = offer_counts[1] if len(offer_counts) > 1 else 0

        # Use the best available price (prefer Amazon, then new 3P)
        best_price = amazon_price or new_3p_price
        category = product.get("categoryTree", [{}])
        category_name = category[0].get("name", "") if category else ""

        return {
            "platform": "amazon",
            "asin": product.get("asin"),
            "title": product.get("title", ""),
            "price": best_price,
            "amazon_price": amazon_price,
            "new_3p_price": new_3p_price,
            "used_price": used_price,
            "avg_price_30d": cents_to_dollars(avg_30) if avg_30 else None,
            "avg_price_90d": cents_to_dollars(avg_90) if avg_90 else None,
            "bsr": bsr,
            "new_offer_count": new_offer_count,
            "used_offer_count": used_offer_count,
            "category": category_name,
            "image_url": f"https://images-na.ssl-images-amazon.com/images/I/{product.get('imagesCSV', '').split(',')[0]}" if product.get("imagesCSV") else None,
            "url": f"https://www.amazon.com/dp/{product.get('asin', '')}",
            "fba_fees": product.get("fbaFees", {}),
            "extra_data": {
                "sales_rank_drops_30": stats.get("salesRankDrops30", 0),
                "sales_rank_drops_90": stats.get("salesRankDrops90", 0),
                "buy_box_seller": product.get("buyBoxSellerIdHistory"),
                "is_sns": product.get("isSubscribeAndSave", False),
            },
        }

    async def _get_cached(self, key: str) -> dict | None:
        try:
            r = await self._get_redis()
            raw = await r.get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            logger.debug("Cache miss/error for %s", key)
        return None

    async def _set_cached(self, key: str, data: dict):
        try:
            r = await self._get_redis()
            await r.set(key, json.dumps(data), ex=CACHE_TTL)
        except Exception:
            logger.debug("Cache set error for %s", key)

    async def close(self):
        await self._http.aclose()
        if self._redis:
            await self._redis.aclose()
