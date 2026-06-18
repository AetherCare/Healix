"""
Timeline aggregation service merging all health event types chronologically.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blood_report import BloodReport
from app.models.doctor_appointment import DoctorAppointment
from app.models.medical_record import MedicalRecord
from app.models.medication import Medication
from app.models.symptom_entry import SymptomEntry
from app.models.wearable_data import WearableData
from app.schemas.timeline import TimelineEvent


async def build_timeline(db: AsyncSession, user_id: UUID, limit: int = 100) -> List[TimelineEvent]:
    """
    Aggregate and sort health events from all data sources.

    Returns:
        Chronologically sorted list of unified timeline events (newest first).
    """
    events: List[TimelineEvent] = []

    symptoms = await db.execute(
        select(SymptomEntry).where(SymptomEntry.user_id == user_id)
    )
    for entry in symptoms.scalars().all():
        events.append(TimelineEvent(
            id=entry.id,
            event_type="symptom",
            title="Journal Entry",
            description=entry.transcript[:200],
            timestamp=entry.timestamp,
            metadata={"symptom_tags": entry.symptom_tags, "mood_tags": entry.mood_tags},
        ))

    records = await db.execute(
        select(MedicalRecord).where(MedicalRecord.user_id == user_id)
    )
    for record in records.scalars().all():
        events.append(TimelineEvent(
            id=record.id,
            event_type="medical_record",
            title=f"Medical Record — {record.category.value}",
            description=record.file_url,
            timestamp=record.upload_date,
            metadata={"category": record.category.value},
        ))

    blood = await db.execute(
        select(BloodReport).where(BloodReport.user_id == user_id)
    )
    for report in blood.scalars().all():
        events.append(TimelineEvent(
            id=report.id,
            event_type="blood_report",
            title="Blood Report Analysis",
            description=report.analysis or "Blood report processed",
            timestamp=datetime.combine(report.report_date, datetime.min.time()),
            metadata={"biomarker_count": len(report.extracted_values.get("biomarkers", {}))},
        ))

    meds = await db.execute(
        select(Medication).where(Medication.user_id == user_id)
    )
    for med in meds.scalars().all():
        events.append(TimelineEvent(
            id=med.id,
            event_type="medication",
            title=f"Medication — {med.medication_name}",
            description=f"{med.dosage}, {med.frequency}",
            timestamp=datetime.combine(med.start_date, datetime.min.time()),
            metadata={"end_date": str(med.end_date) if med.end_date else None},
        ))

    appointments = await db.execute(
        select(DoctorAppointment).where(DoctorAppointment.user_id == user_id)
    )
    for appt in appointments.scalars().all():
        events.append(TimelineEvent(
            id=appt.id,
            event_type="appointment",
            title=f"Appointment — {appt.doctor_name}",
            description=f"{appt.specialty} ({appt.status.value})",
            timestamp=appt.appointment_date,
            metadata={"status": appt.status.value},
        ))

    wearables = await db.execute(
        select(WearableData).where(WearableData.user_id == user_id)
    )
    for w in wearables.scalars().all():
        events.append(TimelineEvent(
            id=w.id,
            event_type="wearable",
            title="Wearable Sync",
            description=f"HR: {w.heart_rate}, SpO2: {w.oxygen}",
            timestamp=w.timestamp,
            metadata={"activity": w.activity},
        ))

    events.sort(key=lambda e: e.timestamp, reverse=True)
    return events[:limit]
