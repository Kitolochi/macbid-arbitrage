import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Text, Numeric, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class AuctionStatus(str, PyEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ItemCondition(str, PyEnum):
    NEW = "new"
    LIKE_NEW = "like_new"
    OPEN_BOX = "open_box"
    DAMAGED = "damaged"
    UNKNOWN = "unknown"


class MacBidListing(Base):
    __tablename__ = "macbid_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    current_bid: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    retail_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    condition: Mapped[ItemCondition] = mapped_column(Enum(ItemCondition), default=ItemCondition.UNKNOWN)
    auction_type: Mapped[str | None] = mapped_column(String(50))
    warehouse_location: Mapped[str | None] = mapped_column(String(100))
    closes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[AuctionStatus] = mapped_column(Enum(AuctionStatus), default=AuctionStatus.ACTIVE)
    url: Mapped[str | None] = mapped_column(Text)
    extra_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product: Mapped["Product"] = relationship(back_populates="listings")
    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="macbid_listing")
