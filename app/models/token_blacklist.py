"""
Refresh token blacklist for explicit logout invalidation.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TokenBlacklist(Base):
    """Revoked JWT identifiers (jti) preventing reuse after logout."""

    __tablename__ = "token_blacklist"

    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
