import logging
import time
import json

import httpx
import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_BROWSE_URL = f"{settings.ebay_api_base}/buy/browse/v1/item_summary/search"

CACHE_TTL = 7200  # 2 hours


class EbayClient:
    """eBay Browse API client with OAuth 2.0 client credentials flow."""

    def __init__(self):
        self._access_token: str | None = None
        self._token_expires_at: float = 0
        self._http = httpx.AsyncClient(timeout=15)
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def _get_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        logger.info("Refreshing eBay OAuth token")
        resp = await self._http.post(
            EBAY_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
            auth=(settings.ebay_client_id, settings.ebay_client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 7200)
        return self._access_token

    async def search_by_upc(self, upc: str) -> list[dict]:
        """Search eBay by UPC. Returns list of item summaries."""
        cache_key = f"ebay:upc:{upc}"
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        token = await self._get_token()
        results = await self._browse_search(
            params={"gtin": upc, "limit": "20"},
            token=token,
        )

        await self._set_cached(cache_key, results)
        return results

    async def search_by_keyword(self, query: str, category_id: str | None = None) -> list[dict]:
        """Search eBay by keyword. Returns list of item summaries."""
        cache_key = f"ebay:kw:{query}:{category_id or ''}"
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        token = await self._get_token()
        params = {"q": query, "limit": "20"}
        if category_id:
            params["category_ids"] = category_id

        results = await self._browse_search(params=params, token=token)
        await self._set_cached(cache_key, results)
        return results

    async def _browse_search(self, params: dict, token: str) -> list[dict]:
        resp = await self._http.get(
            EBAY_BROWSE_URL,
            params=params,
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                "X-EBAY-C-ENDUSERCTX": "affiliateCampaignId=<ePNCampaignId>,affiliateReferenceId=<referenceId>",
            },
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        return self._parse_results(data)

    def _parse_results(self, data: dict) -> list[dict]:
        items = []
        for raw in data.get("itemSummaries", []):
            price_val = raw.get("price", {})
            shipping = raw.get("shippingOptions", [{}])
            shipping_cost = 0.0
            if shipping:
                ship_price = shipping[0].get("shippingCost", {})
                shipping_cost = float(ship_price.get("value", 0))

            condition = raw.get("condition", "")
            item = {
                "platform": "ebay",
                "title": raw.get("title", ""),
                "price": float(price_val.get("value", 0)),
                "currency": price_val.get("currency", "USD"),
                "condition": condition,
                "shipping_cost": shipping_cost,
                "url": raw.get("itemWebUrl", ""),
                "image_url": raw.get("image", {}).get("imageUrl"),
                "item_id": raw.get("itemId"),
                "seller": raw.get("seller", {}).get("username"),
                "extra_data": {
                    "buying_options": raw.get("buyingOptions", []),
                    "item_group_type": raw.get("itemGroupType"),
                    "categories": [
                        c.get("categoryName") for c in raw.get("categories", [])
                    ],
                },
            }
            items.append(item)
        return items

    async def _get_cached(self, key: str) -> list[dict] | None:
        try:
            r = await self._get_redis()
            raw = await r.get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            logger.debug("Cache miss/error for %s", key)
        return None

    async def _set_cached(self, key: str, data: list[dict]):
        try:
            r = await self._get_redis()
            await r.set(key, json.dumps(data), ex=CACHE_TTL)
        except Exception:
            logger.debug("Cache set error for %s", key)

    async def close(self):
        await self._http.aclose()
        if self._redis:
            await self._redis.aclose()
