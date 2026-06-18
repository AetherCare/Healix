"""
User model with role-based access control.
"""

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.blood_report import BloodReport
    from app.models.doctor_appointment import DoctorAppointment
    from app.models.emergency_card import EmergencyCard
    from app.models.family_member import FamilyMember
    from app.models.medical_record import MedicalRecord
    from app.models.medication import Medication
    from app.models.symptom_entry import SymptomEntry
    from app.models.wearable_data import WearableData


class UserRole(str, enum.Enum):
    """RBAC roles for MediVault AI users."""

    USER = "user"
    ADMIN = "admin"
    DOCTOR = "doctor"


class Gender(str, enum.Enum):
    """Supported gender values for user profiles."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class User(Base):
    """Registered platform user with authentication and profile data."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(
        Enum(
            Gender,
            name="gender",
            values_callable=lambda enum: [e.value for e in enum],
            validate_strings=True,
        ),
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="userrole",
            values_callable=lambda enum: [e.value for e in enum],
            validate_strings=True,
        ),
        default=UserRole.USER,
        nullable=False,
    )

    medical_records: Mapped[List["MedicalRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    blood_reports: Mapped[List["BloodReport"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    medications: Mapped[List["Medication"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    symptom_entries: Mapped[List["SymptomEntry"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    appointments: Mapped[List["DoctorAppointment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    family_members: Mapped[List["FamilyMember"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan",
        foreign_keys="FamilyMember.owner_user_id",
    )
    emergency_card: Mapped[Optional["EmergencyCard"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    wearable_data: Mapped[List["WearableData"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
