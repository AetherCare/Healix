"""
Health insights: symptom trends and medication compliance metrics.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.insights import ComplianceMetricsResponse, SymptomTrendsResponse
from app.services.insights_service import get_compliance_metrics, get_symptom_trends

router = APIRouter(prefix="/insights", tags=["Health Insights"])


@router.get("/get_symptom_trends", response_model=SymptomTrendsResponse)
async def symptom_trends(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    period_days: int = 30,
) -> SymptomTrendsResponse:
    """Analyze symptom tag frequency trends over a rolling time window."""
    return await get_symptom_trends(db, current_user.id, period_days)


@router.get("/get_compliance_metrics", response_model=ComplianceMetricsResponse)
async def compliance_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ComplianceMetricsResponse:
    """Calculate medication adherence and compliance rates."""
    return await get_compliance_metrics(db, current_user.id)
