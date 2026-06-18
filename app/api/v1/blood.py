"""
Blood report analysis and history routes.
"""

from datetime import date
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.blood_report import BloodReport
from app.models.user import User
from app.schemas.blood import BloodHistoryResponse, BloodReportResponse
from app.services.file_validation import validate_upload
from app.services.storage import create_storage_backend
from app.tasks.document_tasks import analyze_blood_report_task

router = APIRouter(prefix="/blood", tags=["Blood Reports"])


@router.post("/analyze", response_model=BloodReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_blood(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    report_date: Optional[date] = None,
) -> BloodReportResponse:
    """Upload a blood report for background OCR and AI biomarker extraction."""
    content, mime_type, _ = await validate_upload(file)
    storage = create_storage_backend()
    file_url = await storage.save(content, file.filename or "blood_report", "blood")

    report = BloodReport(
        user_id=current_user.id,
        extracted_values={"status": "processing"},
        analysis="Analysis in progress...",
        report_date=report_date or date.today(),
    )
    db.add(report)
    await db.flush()

    log_audit_event("create", "BloodReport", current_user.id, report.id)

    analyze_blood_report_task.delay(
        str(current_user.id),
        str(report.id),
        file_url,
        mime_type,
    )

    return BloodReportResponse.model_validate(report)


@router.get("/history", response_model=BloodHistoryResponse)
async def blood_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
) -> BloodHistoryResponse:
    """Retrieve historical blood report analyses."""
    base_query = select(BloodReport).where(BloodReport.user_id == current_user.id)
    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        base_query.order_by(BloodReport.report_date.desc()).offset(skip).limit(limit)
    )
    items = [BloodReportResponse.model_validate(r) for r in result.scalars().all()]
    return BloodHistoryResponse(items=items, total=total)
