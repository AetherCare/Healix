"""Health timeline feed schemas."""

from datetime import datetime
from typing import Any, Dict, List, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """Unified chronological health event."""

    id: UUID
    event_type: Literal[
        "symptom", "medication", "appointment", "blood_report", "medical_record", "wearable"
    ]
    title: str
    description: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimelineResponse(BaseModel):
    """Chronological health feed."""

    events: List[TimelineEvent]
    total: int
