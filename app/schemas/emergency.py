"""Emergency health card schemas."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EmergencyCardGenerate(BaseModel):
    """Payload to generate or update emergency card metadata."""

    blood_group: str = Field(..., min_length=1, max_length=8)
    allergies: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)


class EmergencyCardResponse(BaseModel):
    """Emergency card with QR code URL."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    blood_group: str
    allergies: List[str]
    medications: List[str]
    qr_code_url: Optional[str] = None
