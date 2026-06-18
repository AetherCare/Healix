"""
Family member sub-profiles with permission levels.
"""

import enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class PermissionLevel(str, enum.Enum):
    """Access tier for shared family health profiles."""

    VIEW_ONLY = "view_only"
    EDIT = "edit"
    FULL = "full"


class FamilyMember(Base):
    """Family health hub member linked to an owner account."""

    __tablename__ = "family_members"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    owner_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_name: Mapped[str] = mapped_column(String(255), nullable=False)
    relation: Mapped[str] = mapped_column(String(64), nullable=False)
    permission_level: Mapped[PermissionLevel] = mapped_column(
        Enum(PermissionLevel), default=PermissionLevel.VIEW_ONLY, nullable=False
    )

    owner: Mapped["User"] = relationship(
        back_populates="family_members", foreign_keys=[owner_user_id]
    )
