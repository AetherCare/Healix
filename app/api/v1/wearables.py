"""
Wearable device telemetry sync and historical metrics routes.
"""

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.wearable_data import WearableData
from app.schemas.wearables import WearableDataResponse, WearableHistoryResponse, WearableSync

router = APIRouter(prefix="/wearables", tags=["Wearable Integration"])


@router.post("/sync_telemetry", response_model=WearableDataResponse, status_code=status.HTTP_201_CREATED)
async def sync_telemetry(
    payload: WearableSync,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WearableDataResponse:
    """Ingest a wearable telemetry snapshot."""
    entry = WearableData(
        user_id=current_user.id,
        heart_rate=payload.heart_rate,
        sleep=payload.sleep,
        oxygen=payload.oxygen,
        activity=payload.activity,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.flush()
    log_audit_event("create", "WearableData", current_user.id, entry.id)
    return WearableDataResponse.model_validate(entry)


@router.get("/get_historical_metrics", response_model=WearableHistoryResponse)
async def get_historical_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
) -> WearableHistoryResponse:
    """Retrieve historical wearable telemetry for charting."""
    query = select(WearableData).where(WearableData.user_id == current_user.id)
    if from_date:
        query = query.where(WearableData.timestamp >= from_date)
    if to_date:
        query = query.where(WearableData.timestamp <= to_date)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        query.order_by(WearableData.timestamp.desc()).offset(skip).limit(limit)
    )
    items = [WearableDataResponse.model_validate(w) for w in result.scalars().all()]
    return WearableHistoryResponse(items=items, total=total)
