import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upc: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    asin: Mapped[str | None] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    image_url: Mapped[str | None] = mapped_column(Text)
    extra_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    listings: Mapped[list["MacBidListing"]] = relationship(back_populates="product")
    prices: Mapped[list["PlatformPrice"]] = relationship(back_populates="product")
    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="product")
