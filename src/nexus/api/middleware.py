"""Nexus API middleware: request id injection and process timing.

Plain ASGI (not Starlette's ``BaseHTTPMiddleware``): the request and response pass through untouched,
so streamed bodies, exceptions raised while reading the body (for example an app's 413 body size
limit) and background tasks behave exactly as without the middleware.
"""

from __future__ import annotations

import re
import time
import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from nexus import __version__

# A caller supplied id is echoed in headers and logs: accept only a short, plain token.
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def new_request_id() -> str:
    return f"nex-{uuid.uuid4().hex[:12]}"


def accepted_request_id(value: str | None) -> str | None:
    """The caller's request id if it is a plain token of at most 128 characters, else None."""
    if value and _SAFE_REQUEST_ID.match(value):
        return value
    return None


class NexusTelemetryMiddleware:
    """Sets ``request.state.request_id`` and adds request id, framework version and timing headers.

    The id comes from ``X-Request-ID`` or ``X-Nexus-Correlation-ID`` when the caller sends a plain
    token, otherwise a new one is generated.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        incoming = Headers(scope=scope)
        request_id = (
            accepted_request_id(incoming.get("x-request-id"))
            or accepted_request_id(incoming.get("x-nexus-correlation-id"))
            or new_request_id()
        )
        # ``request.state`` reads ``scope["state"]``.
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["X-Nexus-Correlation-ID"] = request_id
                headers["X-Nexus-Framework-Version"] = __version__
                headers["X-Process-Time"] = f"{(time.perf_counter() - started) * 1000.0:.2f}ms"
            await send(message)

        await self.app(scope, receive, send_with_headers)
