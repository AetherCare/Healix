"""Health insights and analytics schemas."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class SymptomTrend(BaseModel):
    """Aggregated symptom frequency over a time window."""

    tag: str
    count: int
    trend_direction: str = Field(description="up, down, or stable")


class SymptomTrendsResponse(BaseModel):
    """Symptom trend analytics."""

    trends: List[SymptomTrend]
    period_days: int


class ComplianceMetricsResponse(BaseModel):
    """Medication adherence metrics."""

    overall_adherence_rate: float
    medications: List[Dict[str, Any]]
    missed_doses_last_30_days: int
