"""
Family health hub member management routes.
"""

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.family_member import FamilyMember
from app.models.user import User
from app.schemas.family import (
    FamilyMemberCreate,
    FamilyMemberResponse,
    FamilyMemberUpdate,
    FamilyProfilesResponse,
)

router = APIRouter(prefix="/family", tags=["Family Health Hub"])


@router.post("/manage_members", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
async def manage_members(
    payload: FamilyMemberCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FamilyMemberResponse:
    """Add a family member sub-profile."""
    member = FamilyMember(
        owner_user_id=current_user.id,
        member_name=payload.member_name,
        relation=payload.relation,
        permission_level=payload.permission_level,
    )
    db.add(member)
    await db.flush()
    log_audit_event("create", "FamilyMember", current_user.id, member.id)
    return FamilyMemberResponse.model_validate(member)


@router.get("/fetch_profiles", response_model=FamilyProfilesResponse)
async def fetch_profiles(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FamilyProfilesResponse:
    """Fetch all family member profiles for the owner account."""
    result = await db.execute(
        select(FamilyMember).where(FamilyMember.owner_user_id == current_user.id)
    )
    members = [FamilyMemberResponse.model_validate(m) for m in result.scalars().all()]
    return FamilyProfilesResponse(members=members)
