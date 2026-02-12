import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Text, Numeric, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Platform(str, PyEnum):
    EBAY = "ebay"
    AMAZON = "amazon"
    FACEBOOK = "facebook"


class PlatformPrice(Base):
    __tablename__ = "platform_prices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    condition: Mapped[str | None] = mapped_column(String(50))
    shipping_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    url: Mapped[str | None] = mapped_column(Text)
    seller_info: Mapped[str | None] = mapped_column(String(200))
    extra_data: Mapped[dict | None] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="prices")
