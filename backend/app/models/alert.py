import uuid
from datetime import datetime

from sqlalchemy import String, Text, Numeric, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AlertSetting(Base):
    __tablename__ = "alert_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    min_profit: Mapped[float] = mapped_column(Numeric(10, 2), default=10.00)
    min_roi: Mapped[float] = mapped_column(Numeric(8, 2), default=20.00)
    watched_categories: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_setting_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alert_settings.id"), nullable=False)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("opportunities.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
