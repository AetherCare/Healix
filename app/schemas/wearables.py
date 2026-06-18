"""Wearable telemetry schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WearableSync(BaseModel):
    """Incoming wearable telemetry payload."""

    heart_rate: Optional[float] = Field(None, ge=0, le=300)
    sleep: Optional[Dict[str, Any]] = None
    oxygen: Optional[float] = Field(None, ge=0, le=100)
    activity: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class WearableDataResponse(BaseModel):
    """Stored wearable telemetry record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    heart_rate: Optional[float] = None
    sleep: Optional[Dict[str, Any]] = None
    oxygen: Optional[float] = None
    activity: Optional[Dict[str, Any]] = None
    timestamp: datetime


class WearableHistoryResponse(BaseModel):
    """Historical wearable metrics."""

    items: List[WearableDataResponse]
    total: int
