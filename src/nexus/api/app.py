"""Nexus API: Standard FastAPI application factory for microservices."""
from __future__ import annotations

import datetime
from typing import Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nexus import __version__
from nexus.api.middleware import NexusTelemetryMiddleware


def create_nexus_app(
    title: str = "Nexus Application",
    description: str = "Application built on the Nexus Framework",
    version: str = "0.1.0",
    cors_origins: list[str] | None = None,
    include_health: bool = True,
) -> FastAPI:
    """Build and configure a production-ready FastAPI app."""
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url="/docs",
        redoc_url=None,
    )

    # CORS
    allowed_origins = cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Telemetry
    app.add_middleware(NexusTelemetryMiddleware)

    if include_health:
        @app.get("/health", tags=["system"])
        async def health_check() -> dict[str, Any]:
            return {
                "status": "ok",
                "app": title,
                "version": version,
                "framework_version": __version__,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

        @app.get("/ready", tags=["system"])
        async def readiness_check() -> dict[str, str]:
            return {"status": "ready"}

    # Standard global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": str(exc),
                "request_id": req_id,
            },
        )

    return app
