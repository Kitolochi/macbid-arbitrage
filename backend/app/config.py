from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://arbitrage:arbitrage_dev@localhost:5432/arbitrage"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"

    # eBay API
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_api_base: str = "https://api.ebay.com"

    # Keepa API
    keepa_api_key: str = ""

    # Resend (email)
    resend_api_key: str = ""
    alert_from_email: str = "alerts@macbid-arbitrage.com"

    # MacBid
    macbid_base_url: str = "https://mac.bid"
    scrape_interval_minutes: int = 10

    # Tax rate (default, can be overridden per-user)
    default_tax_rate: float = 0.06

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
