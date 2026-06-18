"""Journal and voice transcription schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TranscribeResponse(BaseModel):
    """Whisper transcription result."""

    transcript: str
    language: Optional[str] = None


class JournalCreate(BaseModel):
    """Manual or post-transcription journal entry."""

    transcript: str = Field(..., min_length=1)
    symptom_tags: List[str] = Field(default_factory=list)
    mood_tags: List[str] = Field(default_factory=list)


class SymptomEntryResponse(BaseModel):
    """Journal entry response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    transcript: str
    symptom_tags: List[str]
    mood_tags: List[str]
    timestamp: datetime


class JournalHistoryResponse(BaseModel):
    """Paginated journal history."""

    items: List[SymptomEntryResponse]
    total: int
