"""
Voice journal symptom entries with transcript and tag arrays.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class SymptomEntry(Base):
    """Journal entry from voice transcription with symptom and mood tags."""

    __tablename__ = "symptom_entries"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    symptom_tags: Mapped[List[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    mood_tags: Mapped[List[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user: Mapped["User"] = relationship(back_populates="symptom_entries")
