"""
Medical record uploads with category classification and file integrity hashing.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class RecordCategory(str, enum.Enum):
    """Medical document category taxonomy."""

    PRESCRIPTION = "prescription"
    BLOOD_REPORT = "blood_report"
    SCAN = "scan"
    NOTE = "note"
    OTHER = "other"


class MedicalRecord(Base):
    """Uploaded medical document metadata and storage reference."""

    __tablename__ = "medical_records"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[RecordCategory] = mapped_column(Enum(RecordCategory), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="medical_records")
