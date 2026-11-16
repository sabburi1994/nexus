"""Nexus API: Standard FastAPI application factory for microservices."""

from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nexus import __version__
from nexus.ai.spend import AiSpendDisabled, MonthlyBudgetExceeded, SpendLedgerUnavailable
from nexus.api.middleware import NexusTelemetryMiddleware
from nexus.api.ratelimit import RateLimitExceeded
from nexus.api.security_headers import NexusSecurityHeadersMiddleware, SecurityHeadersConfig

logger = logging.getLogger("nexus.api")

INTERNAL_ERROR_MESSAGE = "An internal error occurred. Quote the request id when reporting it."


class InMemoryDbSession:
    """Fallback in-memory mock session for rapid prototyping and tests."""

    def __init__(self) -> None:
        self._store: list[Any] = []

    def query(self, entity: Any) -> Any:
        class QueryHelper:
            def __init__(self, items: list[Any]) -> None:
                self.items = items

            def filter_by(self, **kwargs: Any) -> QueryHelper:
                return self

            def first(self) -> Any:
                return self.items[0] if self.items else None

            def all(self) -> list[Any]:
                return list(self.items)

        return QueryHelper(self._store)

    def add(self, obj: Any) -> None:
        self._store.append(obj)

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


class NexusApp(FastAPI):
    """FastAPI subclass that provides flexible tuple unpacking and default in-memory db."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.db = InMemoryDbSession()

    def __iter__(self) -> Any:
        yield self
        yield self.db


def configure_cors(
    app: FastAPI,
    origins: list[str] | None,
    allow_credentials: bool | None = None,
) -> None:
    """Attach CORS middleware with safe defaults.

    * No origins: nothing is added (same-origin only).
    * Wildcard ``"*"``: allowed, but never with credentials.
    * Explicit origins: credentials allowed unless ``allow_credentials`` is False.
    """
    allowed = [o.strip() for o in (origins or []) if o and o.strip()]
    if not allowed:
        if allow_credentials:
            raise ValueError("CORS credentials require explicit cors_origins.")
        return
    wildcard = "*" in allowed
    if wildcard and allow_credentials:
        raise ValueError("CORS credentials cannot be combined with the '*' origin; list explicit origins.")
    credentials = (not wildcard) if allow_credentials is None else (allow_credentials and not wildcard)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if wildcard else allowed,
        allow_credentials=credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )


def create_nexus_app(
    title: str = "Nexus Application",
    description: str = "Application built on the Nexus Framework",
    version: str = "0.1.0",
    cors_origins: list[str] | None = None,
    include_health: bool = True,
    cors_allow_credentials: bool | None = None,
    security_headers: SecurityHeadersConfig | bool = False,
    docs: bool = True,
    health_path: str = "/health",
    ready_path: str | None = "/ready",
) -> NexusApp:
    """Build and configure a production-ready FastAPI app.

    CORS is closed by default: with no ``cors_origins`` no CORS headers are sent, so only
    same-origin browsers can call the API. Pass explicit origins (for example
    ``["https://app.example.com"]``) to open it. Credentials (cookies, auth headers) are
    allowed only for explicit origins; combining them with ``"*"`` raises ``ValueError``.

    ``security_headers=True`` adds CSP, HSTS, nosniff, ``X-Frame-Options: DENY``, a same-origin
    referrer policy and a restrictive permissions policy (see ``SecurityHeadersConfig``); pass a
    ``SecurityHeadersConfig`` to tune the policy or the static asset cache rules.

    ``docs=False`` removes ``/docs`` and ``/openapi.json`` (recommended for private apps).
    ``health_path`` and ``ready_path`` keep an app's existing probe paths (``ready_path=None`` drops
    the readiness route). See docs/ADOPTING.md for the error contract.
    """
    app = NexusApp(
        title=title,
        description=description,
        version=version,
        docs_url="/docs" if docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs else None,
    )

    # CORS: closed unless origins are configured explicitly.
    configure_cors(app, cors_origins, cors_allow_credentials)

    # Telemetry
    app.add_middleware(NexusTelemetryMiddleware)

    # Security headers (added last, so they also cover responses produced by inner middleware).
    if security_headers:
        config = security_headers if isinstance(security_headers, SecurityHeadersConfig) else SecurityHeadersConfig()
        app.add_middleware(NexusSecurityHeadersMiddleware, config=config)

    if include_health:
        # HEAD as well as GET: uptime checkers and load balancers often probe with HEAD.
        @app.api_route(health_path, methods=["GET", "HEAD"], tags=["system"])
        async def health_check() -> dict[str, Any]:
            return {
                "status": "ok",
                "healthy": True,
                "app": title,
                "version": version,
                "framework_version": __version__,
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            }

        if ready_path:

            @app.api_route(ready_path, methods=["GET", "HEAD"], tags=["system"])
            async def readiness_check() -> dict[str, str]:
                return {"status": "ready"}

    def _request_id(request: Request) -> str:
        return str(getattr(request.state, "request_id", "") or f"nex-{uuid.uuid4().hex[:12]}")

    def _error(request: Request, status: int, error: str, message: str, **extra: Any) -> JSONResponse:
        req_id = _request_id(request)
        headers = {"X-Request-ID": req_id}
        if "retry_after" in extra:
            headers["Retry-After"] = str(extra["retry_after"])
        return JSONResponse(
            status_code=status,
            content={"error": error, "message": message, **extra, "request_id": req_id},
            headers=headers,
        )

    # Nexus error contract for the kit's own exceptions (see docs/ADOPTING.md).
    @app.exception_handler(RateLimitExceeded)
    async def rate_limited_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return _error(request, 429, "rate_limited", exc.message, retry_after=exc.retry_after)

    @app.exception_handler(MonthlyBudgetExceeded)
    async def ai_budget_handler(request: Request, exc: MonthlyBudgetExceeded) -> JSONResponse:
        if isinstance(exc, AiSpendDisabled):
            return _error(request, 429, "ai_disabled", "AI features are switched off for this app.")
        if isinstance(exc, SpendLedgerUnavailable):
            return _error(
                request,
                503,
                "ai_budget_unavailable",
                "AI features are paused because the spend ledger cannot be read. Try again later.",
            )
        return _error(
            request,
            429,
            "ai_budget_exhausted",
            "The monthly AI budget is used up. AI features resume next month.",
            month=exc.month,
        )

    # Standard global exception handler
    # Unhandled errors: the client gets a generic message and the request id, never the exception
    # text (which can carry SQL, file paths, secrets or upstream responses). The full exception is
    # logged server side under the same request id.
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = _request_id(request)
        logger.error(
            "Unhandled %s on %s %s (request_id=%s)",
            type(exc).__name__,
            request.method,
            request.url.path,
            req_id,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": INTERNAL_ERROR_MESSAGE,
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id},
        )

    return app
