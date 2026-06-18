"""
Medication CRUD routes.
"""

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.medication import Medication
from app.models.user import User
from app.schemas.medications import MedicationCreate, MedicationResponse, MedicationUpdate

router = APIRouter(prefix="/medications", tags=["Medications"])


@router.post("", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    payload: MedicationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MedicationResponse:
    """Add a new medication to the user's profile."""
    med = Medication(user_id=current_user.id, **payload.model_dump())
    db.add(med)
    await db.flush()
    log_audit_event("create", "Medication", current_user.id, med.id)
    return MedicationResponse.model_validate(med)


@router.get("", response_model=List[MedicationResponse])
async def list_medications(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[MedicationResponse]:
    """List all medications for the authenticated user."""
    result = await db.execute(
        select(Medication).where(Medication.user_id == current_user.id)
    )
    return [MedicationResponse.model_validate(m) for m in result.scalars().all()]


@router.put("/{medication_id}", response_model=MedicationResponse)
async def update_medication(
    medication_id: UUID,
    payload: MedicationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MedicationResponse:
    """Update an existing medication record."""
    result = await db.execute(
        select(Medication).where(
            Medication.id == medication_id,
            Medication.user_id == current_user.id,
        )
    )
    med = result.scalar_one_or_none()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(med, field, value)

    log_audit_event("update", "Medication", current_user.id, med.id)
    return MedicationResponse.model_validate(med)


@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication(
    medication_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Remove a medication from the user's profile."""
    result = await db.execute(
        select(Medication).where(
            Medication.id == medication_id,
            Medication.user_id == current_user.id,
        )
    )
    med = result.scalar_one_or_none()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    await db.delete(med)
    log_audit_event("delete", "Medication", current_user.id, medication_id)
