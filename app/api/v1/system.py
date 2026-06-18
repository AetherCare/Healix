"""
System administration routes: health check and tunnel URL exposure.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app import __version__
from app.core.config import get_settings
from app.core.deps import get_admin_user
from app.models.user import User
from app.schemas.system import HealthResponse, TunnelUrlResponse
from app.services.tunnel_service import read_tunnel_url

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Public health check endpoint for connectivity validation."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=__version__,
    )


@router.get("/tunnel-url", response_model=TunnelUrlResponse)
async def get_tunnel_url(
    admin_user: Annotated[User, Depends(get_admin_user)],
) -> TunnelUrlResponse:
    """
    Admin-only endpoint returning the current ngrok public tunnel URL.

    Enables the frontend to self-update its API_BASE_URL when ngrok URLs rotate.
    """
    url = read_tunnel_url()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tunnel URL not available. Ensure start_with_tunnel.sh is running.",
        )
    return TunnelUrlResponse(tunnel_url=url)
