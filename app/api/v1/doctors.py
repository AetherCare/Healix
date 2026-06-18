"""
Doctor directory search and appointment booking routes.
"""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.doctor_appointment import DoctorAppointment
from app.models.user import User
from app.schemas.doctors import (
    AppointmentBook,
    AppointmentResponse,
    DoctorDirectoryResponse,
    DoctorProfile,
)

router = APIRouter(prefix="/doctors", tags=["Doctor Connectivity"])

MOCK_DOCTORS: List[DoctorProfile] = [
    DoctorProfile(
        id="doc_001", name="Dr. Sarah Chen", specialty="Cardiology",
        hospital="City General Hospital", rating=4.8,
        available_slots=["2026-06-20T10:00:00", "2026-06-21T14:00:00"],
    ),
    DoctorProfile(
        id="doc_002", name="Dr. Raj Patel", specialty="Endocrinology",
        hospital="Metro Health Center", rating=4.6,
        available_slots=["2026-06-19T09:00:00", "2026-06-22T11:00:00"],
    ),
    DoctorProfile(
        id="doc_003", name="Dr. Emily Watson", specialty="General Practice",
        hospital="Community Clinic", rating=4.9,
        available_slots=["2026-06-18T15:00:00", "2026-06-20T16:00:00"],
    ),
    DoctorProfile(
        id="doc_004", name="Dr. Michael Okonkwo", specialty="Dermatology",
        hospital="Skin & Wellness Institute", rating=4.7,
        available_slots=["2026-06-23T10:00:00"],
    ),
]


@router.get("/query_directory", response_model=DoctorDirectoryResponse)
async def query_directory(
    current_user: Annotated[User, Depends(get_current_user)],
    specialty: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
) -> DoctorDirectoryResponse:
    """Search the doctor directory by specialty or name."""
    doctors = MOCK_DOCTORS
    if specialty:
        doctors = [d for d in doctors if specialty.lower() in d.specialty.lower()]
    if search:
        doctors = [d for d in doctors if search.lower() in d.name.lower()]
    return DoctorDirectoryResponse(doctors=doctors, total=len(doctors))


@router.post("/book_appointment", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    payload: AppointmentBook,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AppointmentResponse:
    """Book a new doctor appointment."""
    appointment = DoctorAppointment(
        user_id=current_user.id,
        doctor_name=payload.doctor_name,
        specialty=payload.specialty,
        appointment_date=payload.appointment_date,
    )
    db.add(appointment)
    await db.flush()
    log_audit_event("create", "DoctorAppointment", current_user.id, appointment.id)
    return AppointmentResponse.model_validate(appointment)


@router.get("/list_appointments", response_model=List[AppointmentResponse])
async def list_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[AppointmentResponse]:
    """List all appointments for the authenticated user."""
    result = await db.execute(
        select(DoctorAppointment)
        .where(DoctorAppointment.user_id == current_user.id)
        .order_by(DoctorAppointment.appointment_date.desc())
    )
    return [AppointmentResponse.model_validate(a) for a in result.scalars().all()]
