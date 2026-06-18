"""Medication CRUD schemas."""

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MedicationCreate(BaseModel):
    """Create medication prescription."""

    medication_name: str = Field(..., min_length=1, max_length=255)
    dosage: str = Field(..., min_length=1, max_length=128)
    frequency: str = Field(..., min_length=1, max_length=128)
    start_date: date
    end_date: Optional[date] = None


class MedicationUpdate(BaseModel):
    """Partial medication update."""

    medication_name: Optional[str] = Field(None, min_length=1, max_length=255)
    dosage: Optional[str] = Field(None, min_length=1, max_length=128)
    frequency: Optional[str] = Field(None, min_length=1, max_length=128)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    compliance_logs: Optional[List[Dict[str, Any]]] = None


class MedicationResponse(BaseModel):
    """Medication record response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    medication_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    compliance_logs: List[Dict[str, Any]]
