from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "arbitrage",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.scrape",
        "app.tasks.lookup",
        "app.tasks.calculate",
        "app.tasks.alerts",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "scrape-macbid-auctions": {
        "task": "app.tasks.scrape.scrape_macbid",
        "schedule": crontab(minute=f"*/{settings.scrape_interval_minutes}"),
    },
    "refresh-opportunities": {
        "task": "app.tasks.calculate.refresh_opportunities",
        "schedule": crontab(minute="*/15"),
    },
    "check-alerts": {
        "task": "app.tasks.alerts.check_and_send_alerts",
        "schedule": crontab(minute="*/20"),
    },
}
