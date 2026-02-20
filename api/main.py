"""Personal Data Hub — FastAPI Backend."""

import hmac
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Public paths that don't require API key
_PUBLIC_PATHS = frozenset({
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/api/status",
    # Add OAuth callback paths
    "/api/health/whoop/callback",
    "/api/health/withings/callback",
    # Add webhook paths
    "/api/health/webhook",
})


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Require X-API-Key header on non-public endpoints."""

    async def dispatch(self, request: Request, call_next):
        # Skip auth if no API key configured (dev mode)
        if not settings.api_key:
            return await call_next(request)

        path = request.url.path.rstrip("/")

        # Allow public paths and OPTIONS requests
        if path in _PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        # Verify API key
        provided = request.headers.get("X-API-Key", "")
        if not provided or not hmac.compare_digest(provided, settings.api_key):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Personal Data Hub API...")

    # TODO: Start background schedulers for data collection
    # if settings.enable_whoop:
    #     from api.collectors.whoop import start_whoop_scheduler
    #     start_whoop_scheduler()

    yield

    logger.info("Shutting down Personal Data Hub API...")
    # TODO: Stop schedulers


app = FastAPI(
    title="Personal Data Hub",
    description="Self-hosted personal data aggregation and visualization platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Add middlewares
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# TODO: Uncomment as you implement routers
# from api.routers import health, social, system
# app.include_router(health.router, prefix="/api/health", tags=["Health"])
# app.include_router(social.router, prefix="/api/social", tags=["Social"])
# app.include_router(system.router, prefix="/api/system", tags=["System"])


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "Personal Data Hub API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "features": {
            "whoop": settings.enable_whoop,
            "apple_health": settings.enable_apple_health,
            "withings": settings.enable_withings,
            "slack": settings.enable_slack,
            "telegram": settings.enable_telegram,
            "google_calendar": settings.enable_google_calendar,
        },
    }


@app.get("/api/status")
async def api_status():
    """Detailed API status."""
    return {
        "status": "operational",
        "version": "0.1.0",
        "environment": settings.environment,
        "database": "connected",  # TODO: Add real DB health check
        "enabled_sources": [
            source
            for source, enabled in {
                "whoop": settings.enable_whoop,
                "apple_health": settings.enable_apple_health,
                "withings": settings.enable_withings,
                "slack": settings.enable_slack,
                "telegram": settings.enable_telegram,
                "google_calendar": settings.enable_google_calendar,
            }.items()
            if enabled
        ],
    }
