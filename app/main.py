"""
MediVault AI — FastAPI application entry point.

Binds to 0.0.0.0:8000 for LAN/tunnel reachability. CORS is WAN-aware via
ALLOWED_ORIGINS environment variable.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.rate_limit import limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
audit_handler = logging.FileHandler("audit.log")
audit_handler.setLevel(logging.INFO)
logging.getLogger("medivault.audit").addHandler(audit_handler)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle hooks."""
    settings = get_settings()
    logging.getLogger(__name__).info(
        "Starting %s v%s [%s] on %s:%d",
        settings.app_name,
        __version__,
        settings.app_env,
        settings.host,
        settings.port,
    )
    yield
    logging.getLogger(__name__).info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory configuring middleware, CORS, and API routes."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        description="MediVault AI — Your Personal Health Operating System API",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # WAN-aware CORS — no fixed LAN IPs; origins from ALLOWED_ORIGINS env var
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)

    application.mount(
        "/app",
        StaticFiles(directory="UI/MediVault AI UI_UX Design/dist", html=True),
        name="frontend",
    )

    @application.get("/app", include_in_schema=False)
    async def frontend_redirect() -> RedirectResponse:
        return RedirectResponse(url="/app/")

    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.get("/", tags=["Root"])
    async def root() -> dict:
        """Root endpoint with API metadata."""
        return {
            "app": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": f"{settings.api_v1_prefix}/system/health",
            "frontend": "/app/",
        }

    return application


app = create_app()
