"""
Wearable device telemetry with indexed timestamps for time-series queries.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class WearableData(Base):
    """Smartwatch telemetry snapshot for a user at a point in time."""

    __tablename__ = "wearable_data"
    __table_args__ = (
        Index("ix_wearable_data_user_timestamp", "user_id", "timestamp"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    heart_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sleep: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    oxygen: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    activity: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user: Mapped["User"] = relationship(back_populates="wearable_data")
