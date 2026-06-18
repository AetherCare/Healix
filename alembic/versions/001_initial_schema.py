"""Initial database schema for MediVault AI."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all MediVault AI tables."""
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.Enum("male", "female", "other", "prefer_not_to_say", name="gender"), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("role", sa.Enum("user", "admin", "doctor", name="userrole"), nullable=False, server_default="user"),
    )

    op.create_table(
        "token_blacklist",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("jti", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "medical_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("category", sa.Enum("prescription", "blood_report", "scan", "note", "other", name="recordcategory"), nullable=False),
        sa.Column("file_url", sa.String(1024), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("upload_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "blood_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("extracted_values", postgresql.JSONB(), nullable=False),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column("report_date", sa.Date(), nullable=False),
    )

    op.create_table(
        "medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("medication_name", sa.String(255), nullable=False),
        sa.Column("dosage", sa.String(128), nullable=False),
        sa.Column("frequency", sa.String(128), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("compliance_logs", postgresql.JSONB(), nullable=False, server_default="[]"),
    )

    op.create_table(
        "symptom_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("symptom_tags", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("mood_tags", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )

    op.create_table(
        "doctor_appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("doctor_name", sa.String(255), nullable=False),
        sa.Column("specialty", sa.String(128), nullable=False),
        sa.Column("appointment_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Enum("scheduled", "confirmed", "completed", "cancelled", "no_show", name="appointmentstatus"), nullable=False, server_default="scheduled"),
    )

    op.create_table(
        "family_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("member_name", sa.String(255), nullable=False),
        sa.Column("relation", sa.String(64), nullable=False),
        sa.Column("permission_level", sa.Enum("view_only", "edit", "full", name="permissionlevel"), nullable=False, server_default="view_only"),
    )

    op.create_table(
        "emergency_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("blood_group", sa.String(8), nullable=False),
        sa.Column("allergies", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("medications", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("qr_code_url", sa.String(1024), nullable=True),
    )

    op.create_table(
        "wearable_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("heart_rate", sa.Float(), nullable=True),
        sa.Column("sleep", postgresql.JSONB(), nullable=True),
        sa.Column("oxygen", sa.Float(), nullable=True),
        sa.Column("activity", postgresql.JSONB(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )
    op.create_index("ix_wearable_data_user_timestamp", "wearable_data", ["user_id", "timestamp"])


def downgrade() -> None:
    """Drop all MediVault AI tables."""
    op.drop_index("ix_wearable_data_user_timestamp", table_name="wearable_data")
    op.drop_table("wearable_data")
    op.drop_table("emergency_cards")
    op.drop_table("family_members")
    op.drop_table("doctor_appointments")
    op.drop_table("symptom_entries")
    op.drop_table("medications")
    op.drop_table("blood_reports")
    op.drop_table("medical_records")
    op.drop_table("token_blacklist")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS gender")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS recordcategory")
    op.execute("DROP TYPE IF EXISTS appointmentstatus")
    op.execute("DROP TYPE IF EXISTS permissionlevel")
