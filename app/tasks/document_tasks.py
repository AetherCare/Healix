"""
Background Celery tasks for document OCR parsing and blood report AI analysis.
"""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.blood_report import BloodReport
from app.services.blood_analysis import analyze_blood_report_text
from app.services.ocr import parse_document
from app.services.storage import create_storage_backend
from app.services.vector_store import embed_and_store
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_sync_session() -> Session:
    """Create a synchronous database session for Celery worker context."""
    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(sync_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@celery_app.task(name="process_medical_document", bind=True, max_retries=3)
def process_medical_document(
    self,
    user_id: str,
    record_id: str,
    file_url: str,
    mime_type: str,
) -> dict:
    """
    Background task: OCR/parse uploaded medical document and index in ChromaDB.

    Args:
        user_id: Owner user UUID string.
        record_id: Medical record UUID string.
        file_url: Storage URL of the uploaded file.
        mime_type: Detected MIME type.
    """
    try:
        storage = create_storage_backend()
        content = asyncio.run(storage.read(file_url))
        text = parse_document(content, mime_type)

        if text.strip():
            embed_and_store(
                user_id=UUID(user_id),
                text=text,
                source_type="medical_record",
                source_id=record_id,
                metadata={"mime_type": mime_type},
            )

        logger.info("Processed medical document %s for user %s", record_id, user_id)
        return {"status": "completed", "record_id": record_id, "text_length": len(text)}
    except Exception as exc:
        logger.error("Document processing failed: %s", exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="analyze_blood_report", bind=True, max_retries=3)
def analyze_blood_report_task(
    self,
    user_id: str,
    report_id: str,
    file_url: str,
    mime_type: str,
) -> dict:
    """
    Background task: OCR blood report, run LLM biomarker extraction, update DB.

    Args:
        user_id: Owner user UUID string.
        report_id: BloodReport UUID string.
        file_url: Storage URL of the uploaded report.
        mime_type: Detected MIME type.
    """
    session = _get_sync_session()
    try:
        storage = create_storage_backend()
        content = asyncio.run(storage.read(file_url))
        text = parse_document(content, mime_type)

        analysis_result = asyncio.run(analyze_blood_report_text(text))

        result = session.execute(
            select(BloodReport).where(BloodReport.id == UUID(report_id))
        )
        report = result.scalar_one_or_none()
        if report:
            report.extracted_values = analysis_result
            report.analysis = analysis_result.get("summary", "")
            session.commit()

        if text.strip():
            embed_and_store(
                user_id=UUID(user_id),
                text=text,
                source_type="blood_report",
                source_id=report_id,
            )

        logger.info("Blood report analysis completed for %s", report_id)
        return {"status": "completed", "report_id": report_id}
    except Exception as exc:
        session.rollback()
        logger.error("Blood report analysis failed: %s", exc)
        raise self.retry(exc=exc, countdown=30)
    finally:
        session.close()
