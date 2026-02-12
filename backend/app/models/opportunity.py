import uuid
from datetime import datetime

from sqlalchemy import String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    macbid_listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("macbid_listings.id"), nullable=False)
    buy_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    estimated_sell_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sell_platform: Mapped[str] = mapped_column(String(20), nullable=False)
    platform_fees: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    shipping_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    profit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    roi_pct: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product: Mapped["Product"] = relationship(back_populates="opportunities")
    macbid_listing: Mapped["MacBidListing"] = relationship(back_populates="opportunities")
