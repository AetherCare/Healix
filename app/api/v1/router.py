"""
Aggregate all v1 API routers into a single router for mounting.
"""

from fastapi import APIRouter

from app.api.v1 import (
    ai,
    auth,
    blood,
    doctors,
    emergency,
    family,
    insights,
    journal,
    medications,
    records,
    system,
    timeline,
    wearables,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(records.router)
api_router.include_router(blood.router)
api_router.include_router(journal.router)
api_router.include_router(timeline.router)
api_router.include_router(ai.router)
api_router.include_router(insights.router)
api_router.include_router(medications.router)
api_router.include_router(doctors.router)
api_router.include_router(family.router)
api_router.include_router(wearables.router)
api_router.include_router(emergency.router)
api_router.include_router(system.router)
