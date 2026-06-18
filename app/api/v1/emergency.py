"""
Emergency health card routes with QR code generation.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.emergency_card import EmergencyCard
from app.models.user import User
from app.schemas.emergency import EmergencyCardGenerate, EmergencyCardResponse
from app.services.emergency_service import generate_qr_code

router = APIRouter(prefix="/emergency-card", tags=["Emergency Center"])


@router.get("/fetch", response_model=EmergencyCardResponse)
async def fetch_emergency_card(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> EmergencyCardResponse:
    """Retrieve the user's emergency health card."""
    result = await db.execute(
        select(EmergencyCard).where(EmergencyCard.user_id == current_user.id)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergency card not found")
    return EmergencyCardResponse.model_validate(card)


@router.post("/generate_metadata", response_model=EmergencyCardResponse)
async def generate_metadata(
    payload: EmergencyCardGenerate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> EmergencyCardResponse:
    """Generate or update emergency card metadata and QR code."""
    result = await db.execute(
        select(EmergencyCard).where(EmergencyCard.user_id == current_user.id)
    )
    card = result.scalar_one_or_none()

    qr_url = await generate_qr_code(current_user.id, payload.model_dump())

    is_new = card is None
    if card:
        card.blood_group = payload.blood_group
        card.allergies = payload.allergies
        card.medications = payload.medications
        card.qr_code_url = qr_url
    else:
        card = EmergencyCard(
            user_id=current_user.id,
            blood_group=payload.blood_group,
            allergies=payload.allergies,
            medications=payload.medications,
            qr_code_url=qr_url,
        )
        db.add(card)

    await db.flush()
    log_audit_event("create" if is_new else "update", "EmergencyCard", current_user.id, card.id)
    return EmergencyCardResponse.model_validate(card)
