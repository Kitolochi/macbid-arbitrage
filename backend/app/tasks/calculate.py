"""Celery tasks for computing arbitrage opportunities."""

import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.celery_config import celery_app
from app.config import get_settings
from app.services.opportunity import refresh_all_opportunities

logger = logging.getLogger(__name__)
settings = get_settings()


async def _refresh():
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        count = await refresh_all_opportunities(db)
        logger.info("Refreshed %d opportunities", count)


@celery_app.task(name="app.tasks.calculate.refresh_opportunities")
def refresh_opportunities():
    """Recompute arbitrage opportunities for all active listings."""
    asyncio.run(_refresh())
