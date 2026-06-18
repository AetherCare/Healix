"""Blood report analysis schemas."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BloodAnalyzeRequest(BaseModel):
    """Optional metadata when triggering blood report analysis."""

    report_date: Optional[date] = None
    record_id: Optional[UUID] = None


class BloodReportResponse(BaseModel):
    """Structured blood report with AI analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    extracted_values: Dict[str, Any]
    analysis: Optional[str] = None
    report_date: date


class BloodHistoryResponse(BaseModel):
    """Historical blood report collection."""

    items: List[BloodReportResponse]
    total: int
