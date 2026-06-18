"""
AI health assistant chat route with SSE streaming and RAG context.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.ai import ChatRequest
from app.services.chat_service import stream_health_chat

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """
    Stream AI health assistant responses via Server-Sent Events.

    Responses are augmented with ChromaDB RAG context, medication data,
    and recent wearable telemetry.
    """
    return StreamingResponse(
        stream_health_chat(db, current_user.id, payload.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
