import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5


class BaseScraper(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def scrape(self) -> list[dict]:
        """Run the scraper and return a list of raw item dicts."""

    async def run(self) -> list[dict]:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self.logger.info("Scrape attempt %d/%d", attempt, MAX_RETRIES)
                results = await self.scrape()
                self.logger.info("Scraped %d items", len(results))
                return results
            except Exception:
                self.logger.exception("Scrape attempt %d failed", attempt)
                if attempt == MAX_RETRIES:
                    raise
                import asyncio
                await asyncio.sleep(RETRY_DELAY * attempt)
        return []
