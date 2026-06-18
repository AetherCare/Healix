"""System administration schemas."""

from pydantic import BaseModel


class TunnelUrlResponse(BaseModel):
    """Current ngrok public tunnel URL."""

    tunnel_url: str
    source: str = "ngrok"


class HealthResponse(BaseModel):
    """Service health check response."""

    status: str
    app_name: str
    version: str
