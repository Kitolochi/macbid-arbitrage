"""Celery tasks for checking alert thresholds and sending notifications."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta

import resend
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.celery_config import celery_app
from app.config import get_settings
from app.models.alert import AlertSetting, AlertHistory
from app.models.opportunity import Opportunity
from app.models.product import Product
from app.models.listing import MacBidListing

logger = logging.getLogger(__name__)
settings = get_settings()


async def _check_and_send():
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    if not settings.resend_api_key:
        logger.debug("Resend API key not configured, skipping alerts")
        return

    resend.api_key = settings.resend_api_key

    async with Session() as db:
        # Get all active alert settings
        result = await db.execute(
            select(AlertSetting).where(AlertSetting.is_active == True)
        )
        alert_settings = result.scalars().all()

        for alert in alert_settings:
            # Find opportunities matching this alert's thresholds
            query = select(Opportunity).where(
                and_(
                    Opportunity.profit >= float(alert.min_profit),
                    Opportunity.roi_pct >= float(alert.min_roi),
                )
            )
            result = await db.execute(query)
            opportunities = result.scalars().all()

            for opp in opportunities:
                # Check if we already sent an alert for this opportunity
                existing = await db.execute(
                    select(AlertHistory).where(
                        and_(
                            AlertHistory.alert_setting_id == alert.id,
                            AlertHistory.opportunity_id == opp.id,
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                # Get product and listing details for the email
                product = await db.get(Product, opp.product_id)
                listing = await db.get(MacBidListing, opp.macbid_listing_id)

                if not product or not listing:
                    continue

                # Send email
                subject = f"Arbitrage Alert: ${opp.profit:.2f} profit ({opp.roi_pct:.0f}% ROI) - {product.title[:50]}"
                html = _build_alert_email(product, listing, opp)

                try:
                    resend.Emails.send({
                        "from": settings.alert_from_email,
                        "to": alert.email,
                        "subject": subject,
                        "html": html,
                    })

                    # Record that we sent this alert
                    history = AlertHistory(
                        id=uuid.uuid4(),
                        alert_setting_id=alert.id,
                        opportunity_id=opp.id,
                        email=alert.email,
                        subject=subject,
                    )
                    db.add(history)
                    logger.info("Sent alert to %s for opportunity %s", alert.email, opp.id)
                except Exception:
                    logger.exception("Failed to send alert email to %s", alert.email)

        await db.commit()


def _build_alert_email(product, listing, opp) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #16a34a;">Arbitrage Opportunity Found!</h2>
        <div style="background: #f9fafb; border-radius: 8px; padding: 16px; margin: 16px 0;">
            <h3>{product.title}</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>MacBid Current Bid</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${float(listing.current_bid):.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>Total Buy Cost</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${float(opp.buy_cost):.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>Est. Sell Price ({opp.sell_platform})</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${float(opp.estimated_sell_price):.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>Platform Fees</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${float(opp.platform_fees):.2f}</td>
                </tr>
                <tr style="background: #dcfce7;">
                    <td style="padding: 8px;"><strong>Estimated Profit</strong></td>
                    <td style="padding: 8px;"><strong style="color: #16a34a;">${float(opp.profit):.2f}</strong></td>
                </tr>
                <tr style="background: #dcfce7;">
                    <td style="padding: 8px;"><strong>ROI</strong></td>
                    <td style="padding: 8px;"><strong style="color: #16a34a;">{float(opp.roi_pct):.1f}%</strong></td>
                </tr>
            </table>
        </div>
        <a href="{listing.url}" style="display: inline-block; background: #2563eb; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin-top: 8px;">
            View on MacBid
        </a>
    </div>
    """


@celery_app.task(name="app.tasks.alerts.check_and_send_alerts")
def check_and_send_alerts():
    """Check all alert settings against current opportunities and send notifications."""
    asyncio.run(_check_and_send())
