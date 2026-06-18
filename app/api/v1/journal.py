"""
Voice journal transcription and symptom entry routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.symptom_entry import SymptomEntry
from app.models.user import User
from app.schemas.journal import (
    JournalCreate,
    JournalHistoryResponse,
    SymptomEntryResponse,
    TranscribeResponse,
)
from app.services.file_validation import validate_upload
from app.services.vector_store import embed_and_store
from app.services.whisper_service import transcribe_audio

router = APIRouter(prefix="/journal", tags=["Health Journal"])


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_journal(
    current_user: Annotated[User, Depends(get_current_user)],
    audio: UploadFile = File(...),
) -> TranscribeResponse:
    """Transcribe audio via Groq Whisper API."""
    content, _, _ = await validate_upload(audio)
    transcript, language = await transcribe_audio(content, audio.filename or "audio.webm")
    return TranscribeResponse(transcript=transcript, language=language)


@router.post("/create", response_model=SymptomEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    payload: JournalCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SymptomEntryResponse:
    """Create a journal entry and index it in the health memory vector store."""
    entry = SymptomEntry(
        user_id=current_user.id,
        transcript=payload.transcript,
        symptom_tags=payload.symptom_tags,
        mood_tags=payload.mood_tags,
    )
    db.add(entry)
    await db.flush()

    embed_and_store(
        user_id=current_user.id,
        text=payload.transcript,
        source_type="journal",
        source_id=str(entry.id),
        metadata={"symptom_tags": payload.symptom_tags},
    )

    log_audit_event("create", "SymptomEntry", current_user.id, entry.id)
    return SymptomEntryResponse.model_validate(entry)


@router.get("/history", response_model=JournalHistoryResponse)
async def journal_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
) -> JournalHistoryResponse:
    """List journal entries for the authenticated user."""
    base_query = select(SymptomEntry).where(SymptomEntry.user_id == current_user.id)
    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        base_query.order_by(SymptomEntry.timestamp.desc()).offset(skip).limit(limit)
    )
    items = [SymptomEntryResponse.model_validate(e) for e in result.scalars().all()]
    return JournalHistoryResponse(items=items, total=total)
