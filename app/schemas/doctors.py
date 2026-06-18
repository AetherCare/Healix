"""Doctor directory and appointment schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.doctor_appointment import AppointmentStatus


class DoctorProfile(BaseModel):
    """Mock doctor directory entry."""

    id: str
    name: str
    specialty: str
    hospital: str
    rating: float
    available_slots: List[str]


class DoctorDirectoryResponse(BaseModel):
    """Searchable doctor directory."""

    doctors: List[DoctorProfile]
    total: int


class AppointmentBook(BaseModel):
    """Book a new doctor appointment."""

    doctor_name: str = Field(..., min_length=1, max_length=255)
    specialty: str = Field(..., min_length=1, max_length=128)
    appointment_date: datetime


class AppointmentResponse(BaseModel):
    """Appointment record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    doctor_name: str
    specialty: str
    appointment_date: datetime
    status: AppointmentStatus
