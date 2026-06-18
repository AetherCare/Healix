"""
Blood report analysis results with structured biomarker JSONB storage.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class BloodReport(Base):
    """AI-extracted blood biomarker values and narrative analysis."""

    __tablename__ = "blood_reports"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    extracted_values: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)

    user: Mapped["User"] = relationship(back_populates="blood_reports")
