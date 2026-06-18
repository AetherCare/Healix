"""
Chronological health timeline feed route.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.timeline import TimelineResponse
from app.services.timeline_service import build_timeline

router = APIRouter(prefix="/timeline", tags=["Health Timeline"])


@router.get("/get_chronological_feed", response_model=TimelineResponse)
async def get_chronological_feed(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 100,
) -> TimelineResponse:
    """Return a unified chronological feed of all health events."""
    events = await build_timeline(db, current_user.id, limit=limit)
    return TimelineResponse(events=events, total=len(events))
