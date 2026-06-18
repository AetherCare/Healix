"""
Emergency health card with QR code for lock-screen bypass access.
"""

from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class EmergencyCard(Base):
    """Critical health information card with scannable QR code."""

    __tablename__ = "emergency_cards"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    blood_group: Mapped[str] = mapped_column(String(8), nullable=False)
    allergies: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    medications: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    qr_code_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    user: Mapped["User"] = relationship(back_populates="emergency_card")
