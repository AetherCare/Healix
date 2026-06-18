"""AI chat streaming schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """User message for RAG-augmented health assistant."""

    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None


class ChatCitation(BaseModel):
    """RAG source citation anchor."""

    source_type: str
    source_id: str
    excerpt: str
    relevance_score: float
