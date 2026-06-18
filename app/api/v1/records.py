"""
Medical record upload, listing, retrieval, and deletion routes.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.medical_record import MedicalRecord, RecordCategory
from app.models.user import User
from app.schemas.records import MedicalRecordListResponse, MedicalRecordResponse
from app.services.file_validation import validate_upload
from app.services.storage import create_storage_backend
from app.services.vector_store import embed_and_store
from app.tasks.document_tasks import process_medical_document

router = APIRouter(prefix="/records", tags=["Medical Records"])


@router.post("/upload", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def upload_record(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    category: RecordCategory = Form(RecordCategory.OTHER),
) -> MedicalRecordResponse:
    """Upload a medical document with MIME validation and integrity hashing."""
    content, mime_type, file_hash = await validate_upload(file)
    storage = create_storage_backend()
    file_url = await storage.save(content, file.filename or "document", "records")

    record = MedicalRecord(
        user_id=current_user.id,
        category=category,
        file_url=file_url,
        file_hash=file_hash,
    )
    db.add(record)
    await db.flush()

    log_audit_event("create", "MedicalRecord", current_user.id, record.id, {"category": category.value})

    process_medical_document.delay(
        str(current_user.id),
        str(record.id),
        file_url,
        mime_type,
    )

    return MedicalRecordResponse.model_validate(record)


@router.get("", response_model=MedicalRecordListResponse)
async def list_records(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    category: Optional[RecordCategory] = None,
    skip: int = 0,
    limit: int = 50,
) -> MedicalRecordListResponse:
    """List medical records for the authenticated user."""
    query = select(MedicalRecord).where(MedicalRecord.user_id == current_user.id)
    if category:
        query = query.where(MedicalRecord.category == category)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    result = await db.execute(query.order_by(MedicalRecord.upload_date.desc()).offset(skip).limit(limit))
    items = [MedicalRecordResponse.model_validate(r) for r in result.scalars().all()]
    return MedicalRecordListResponse(items=items, total=total)


@router.get("/{record_id}", response_model=MedicalRecordResponse)
async def get_record(
    record_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MedicalRecordResponse:
    """Retrieve a single medical record by ID."""
    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.id == record_id,
            MedicalRecord.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return MedicalRecordResponse.model_validate(record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a medical record and its stored file."""
    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.id == record_id,
            MedicalRecord.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    storage = create_storage_backend()
    await storage.delete(record.file_url)
    await db.delete(record)

    log_audit_event("delete", "MedicalRecord", current_user.id, record_id)
