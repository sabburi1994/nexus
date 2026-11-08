"""Nexus API middleware: Request ID injection and process timing."""
from __future__ import annotations

import time
import uuid
from typing import Awaitable, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class NexusTelemetryMiddleware(BaseHTTPMiddleware):
    """Injects X-Request-ID and X-Process-Time headers on every response."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        request.state.request_id = request_id

        response = await call_next(request)

        duration = time.perf_counter() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration * 1000.0:.2f}ms"
        return response
