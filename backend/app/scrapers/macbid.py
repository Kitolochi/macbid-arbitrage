import json
import logging
from datetime import datetime, timezone

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MacBidScraper(BaseScraper):
    """Scrape mac.bid auction listings using Playwright.

    MacBid is a Next.js app. We extract the __NEXT_DATA__ JSON embedded
    in each page which contains the full server-side-rendered auction data.
    We also intercept XHR requests to the underlying API for paginated
    listing data.
    """

    BASE_URL = settings.macbid_base_url

    async def scrape(self) -> list[dict]:
        items: list[dict] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                )
            )

            # Intercept API responses for auction data
            api_responses: list[dict] = []

            async def handle_response(response):
                url = response.url
                if "api.macdiscount.com" in url and "auction" in url.lower():
                    try:
                        data = await response.json()
                        api_responses.append(data)
                    except Exception:
                        pass

            page = await context.new_page()
            page.on("response", handle_response)

            # Navigate to the main auction listing page
            await page.goto(f"{self.BASE_URL}/auctions", wait_until="networkidle", timeout=30000)

            # Extract __NEXT_DATA__ from the page
            next_data = await self._extract_next_data(page)
            if next_data:
                items.extend(self._parse_next_data(next_data))

            # Also parse any intercepted API responses
            for api_data in api_responses:
                items.extend(self._parse_api_response(api_data))

            # Scroll to trigger lazy-loaded content
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1000)

            # Re-extract after scrolling
            next_data = await self._extract_next_data(page)
            if next_data:
                new_items = self._parse_next_data(next_data)
                existing_ids = {i["listing_id"] for i in items}
                for item in new_items:
                    if item["listing_id"] not in existing_ids:
                        items.append(item)

            await browser.close()

        logger.info("MacBid scrape complete: %d items found", len(items))
        return items

    async def _extract_next_data(self, page) -> dict | None:
        try:
            element = await page.query_selector("script#__NEXT_DATA__")
            if element:
                raw = await element.inner_text()
                return json.loads(raw)
        except Exception:
            logger.exception("Failed to extract __NEXT_DATA__")
        return None

    def _parse_next_data(self, data: dict) -> list[dict]:
        items = []
        try:
            page_props = data.get("props", {}).get("pageProps", {})
            # The exact structure depends on MacBid's current schema.
            # Common patterns: pageProps.auctions, pageProps.items, pageProps.lots
            for key in ("auctions", "items", "lots", "listings"):
                raw_items = page_props.get(key, [])
                if isinstance(raw_items, list):
                    for raw in raw_items:
                        parsed = self._normalize_item(raw)
                        if parsed:
                            items.append(parsed)
            # Also check nested dehydratedState (React Query cache)
            dehydrated = page_props.get("dehydratedState", {})
            for query in dehydrated.get("queries", []):
                query_data = query.get("state", {}).get("data", {})
                if isinstance(query_data, list):
                    for raw in query_data:
                        parsed = self._normalize_item(raw)
                        if parsed:
                            items.append(parsed)
                elif isinstance(query_data, dict):
                    for key in ("items", "lots", "auctions", "results"):
                        for raw in query_data.get(key, []):
                            parsed = self._normalize_item(raw)
                            if parsed:
                                items.append(parsed)
        except Exception:
            logger.exception("Failed to parse __NEXT_DATA__")
        return items

    def _parse_api_response(self, data: dict) -> list[dict]:
        items = []
        try:
            raw_items = data if isinstance(data, list) else data.get("items", data.get("lots", []))
            for raw in raw_items:
                parsed = self._normalize_item(raw)
                if parsed:
                    items.append(parsed)
        except Exception:
            logger.exception("Failed to parse API response")
        return items

    def _normalize_item(self, raw: dict) -> dict | None:
        """Normalize a raw auction item dict into our standard schema."""
        if not isinstance(raw, dict):
            return None

        listing_id = str(
            raw.get("id")
            or raw.get("lotId")
            or raw.get("lot_id")
            or raw.get("auctionId")
            or ""
        )
        if not listing_id:
            return None

        title = raw.get("title") or raw.get("name") or raw.get("description") or ""

        current_bid = self._parse_price(
            raw.get("currentBid")
            or raw.get("current_bid")
            or raw.get("highBid")
            or raw.get("price")
            or 0
        )

        retail_price = self._parse_price(
            raw.get("retailPrice")
            or raw.get("retail_price")
            or raw.get("msrp")
            or raw.get("originalPrice")
        )

        condition_raw = str(
            raw.get("condition") or raw.get("itemCondition") or "unknown"
        ).lower()
        condition_map = {
            "new": "new",
            "like new": "like_new",
            "like_new": "like_new",
            "open box": "open_box",
            "open_box": "open_box",
            "damaged": "damaged",
            "salvage": "damaged",
        }
        condition = condition_map.get(condition_raw, "unknown")

        upc = raw.get("upc") or raw.get("barcode") or raw.get("UPC")
        image_url = raw.get("imageUrl") or raw.get("image") or raw.get("primaryImage")
        if isinstance(image_url, list) and image_url:
            image_url = image_url[0]

        closes_at = raw.get("closesAt") or raw.get("endTime") or raw.get("closes_at")
        if isinstance(closes_at, str):
            try:
                closes_at = datetime.fromisoformat(closes_at.replace("Z", "+00:00"))
            except ValueError:
                closes_at = None

        warehouse = (
            raw.get("warehouse")
            or raw.get("warehouseLocation")
            or raw.get("location")
        )

        return {
            "listing_id": listing_id,
            "title": title,
            "current_bid": current_bid,
            "retail_price": retail_price,
            "condition": condition,
            "upc": str(upc) if upc else None,
            "image_url": image_url,
            "closes_at": closes_at,
            "warehouse_location": warehouse,
            "url": f"{self.BASE_URL}/auction/{listing_id}",
            "extra_data": raw,
        }

    @staticmethod
    def _parse_price(val) -> float | None:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            cleaned = val.replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return None
        if isinstance(val, dict):
            return float(val.get("amount", 0))
        return None
