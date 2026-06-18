"""Family health hub schemas."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.family_member import PermissionLevel


class FamilyMemberCreate(BaseModel):
    """Add a family member sub-profile."""

    member_name: str = Field(..., min_length=1, max_length=255)
    relation: str = Field(..., min_length=1, max_length=64)
    permission_level: PermissionLevel = PermissionLevel.VIEW_ONLY


class FamilyMemberUpdate(BaseModel):
    """Update family member permissions."""

    member_name: Optional[str] = Field(None, min_length=1, max_length=255)
    relation: Optional[str] = Field(None, min_length=1, max_length=64)
    permission_level: Optional[PermissionLevel] = None


class FamilyMemberResponse(BaseModel):
    """Family member profile."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: UUID
    member_name: str
    relation: str
    permission_level: PermissionLevel


class FamilyProfilesResponse(BaseModel):
    """All family members for an owner."""

    members: List[FamilyMemberResponse]
