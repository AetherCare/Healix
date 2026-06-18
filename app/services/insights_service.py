"""
Health insights: symptom trend analysis and medication compliance metrics.
"""

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medication import Medication
from app.models.symptom_entry import SymptomEntry
from app.schemas.insights import ComplianceMetricsResponse, SymptomTrend, SymptomTrendsResponse


async def get_symptom_trends(
    db: AsyncSession,
    user_id,
    period_days: int = 30,
) -> SymptomTrendsResponse:
    """
    Compute symptom tag frequency trends over a rolling time window.

    Compares current period against the prior period of equal length.
    """
    now = datetime.now(timezone.utc)
    current_start = now - timedelta(days=period_days)
    prior_start = current_start - timedelta(days=period_days)

    current_result = await db.execute(
        select(SymptomEntry).where(
            SymptomEntry.user_id == user_id,
            SymptomEntry.timestamp >= current_start,
        )
    )
    prior_result = await db.execute(
        select(SymptomEntry).where(
            SymptomEntry.user_id == user_id,
            SymptomEntry.timestamp >= prior_start,
            SymptomEntry.timestamp < current_start,
        )
    )

    current_tags: Counter = Counter()
    for entry in current_result.scalars().all():
        current_tags.update(entry.symptom_tags)

    prior_tags: Counter = Counter()
    for entry in prior_result.scalars().all():
        prior_tags.update(entry.symptom_tags)

    trends: List[SymptomTrend] = []
    all_tags = set(current_tags.keys()) | set(prior_tags.keys())
    for tag in all_tags:
        current_count = current_tags.get(tag, 0)
        prior_count = prior_tags.get(tag, 0)
        if current_count > prior_count:
            direction = "up"
        elif current_count < prior_count:
            direction = "down"
        else:
            direction = "stable"
        trends.append(SymptomTrend(tag=tag, count=current_count, trend_direction=direction))

    trends.sort(key=lambda t: t.count, reverse=True)
    return SymptomTrendsResponse(trends=trends, period_days=period_days)


async def get_compliance_metrics(
    db: AsyncSession,
    user_id,
) -> ComplianceMetricsResponse:
    """
    Calculate medication adherence rates from compliance log entries.
    """
    result = await db.execute(
        select(Medication).where(Medication.user_id == user_id)
    )
    medications = result.scalars().all()

    med_metrics: List[Dict[str, Any]] = []
    total_taken = 0
    total_expected = 0
    missed = 0

    for med in medications:
        logs = med.compliance_logs or []
        taken = sum(1 for log in logs if log.get("taken", False))
        expected = len(logs) if logs else 1
        rate = (taken / expected * 100) if expected > 0 else 0.0
        med_missed = sum(1 for log in logs if not log.get("taken", False))
        total_taken += taken
        total_expected += expected
        missed += med_missed
        med_metrics.append({
            "medication_name": med.medication_name,
            "adherence_rate": round(rate, 1),
            "doses_logged": len(logs),
        })

    overall = (total_taken / total_expected * 100) if total_expected > 0 else 0.0
    return ComplianceMetricsResponse(
        overall_adherence_rate=round(overall, 1),
        medications=med_metrics,
        missed_doses_last_30_days=missed,
    )
