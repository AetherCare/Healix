"""Medical record upload and listing schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.medical_record import RecordCategory


class MedicalRecordResponse(BaseModel):
    """Medical record metadata response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    category: RecordCategory
    file_url: str
    file_hash: str
    upload_date: datetime


class MedicalRecordListResponse(BaseModel):
    """Paginated list of medical records."""

    items: List[MedicalRecordResponse]
    total: int
