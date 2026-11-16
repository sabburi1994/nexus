"""Regression: an app's body size limit (413) must survive the Nexus request id middleware.

TandemPath's limiter raises ``HTTPException(413)`` from the receive channel. When the request id
middleware was a Starlette ``BaseHTTPMiddleware``, an oversized upload came back as 400 "There was an
error parsing the body". The middleware is plain ASGI since 0.5.0.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from nexus.api import create_nexus_app
from nexus.api.middleware import NexusTelemetryMiddleware

LIMIT = 64 * 1024


class BodySizeLimit:
    """Counts request body bytes as they are received and raises 413 past ``limit``."""

    def __init__(self, app: ASGIApp, limit: int = LIMIT) -> None:
        self.app = app
        self.limit = limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        seen = 0

        async def limited_receive() -> Message:
            nonlocal seen
            message = await receive()
            if message["type"] == "http.request":
                seen += len(message.get("body", b""))
                if seen > self.limit:
                    raise HTTPException(status_code=413, detail="Request body too large")
            return message

        await self.app(scope, limited_receive, send)


def _client() -> TestClient:
    app = create_nexus_app(title="Uploads")
    app.add_middleware(BodySizeLimit)

    @app.post("/api/items")
    async def create(request: Request) -> dict[str, int]:
        payload = await request.json()
        return {"size": len(payload["blob"])}

    @app.post("/api/upload")
    async def upload(request: Request) -> dict[str, int]:
        total = 0
        async for chunk in request.stream():
            total += len(chunk)
        return {"bytes": total}

    return TestClient(app, raise_server_exceptions=False)


def _chunks(total: int, size: int = 8192) -> Iterator[bytes]:
    sent = 0
    while sent < total:
        piece = min(size, total - sent)
        sent += piece
        yield b"x" * piece


def test_small_bodies_pass_and_carry_the_request_id() -> None:
    resp = _client().post("/api/items", json={"blob": "a" * 100}, headers={"X-Request-ID": "req-7"})
    assert resp.status_code == 200 and resp.json() == {"size": 100}
    assert resp.headers["X-Request-ID"] == "req-7"
    assert "X-Process-Time" in resp.headers


def test_oversized_json_body_is_413_not_400() -> None:
    body = json.dumps({"blob": "a" * (LIMIT * 2)})
    resp = _client().post("/api/items", content=body, headers={"content-type": "application/json"})
    assert resp.status_code == 413, resp.text
    assert resp.json() == {"detail": "Request body too large"}


def test_oversized_streamed_upload_is_413_not_400() -> None:
    resp = _client().post("/api/upload", content=_chunks(LIMIT * 4))
    assert resp.status_code == 413, resp.text


@pytest.mark.parametrize("bad", ["has space", "x" * 129, "tab\there", "<script>"])
def test_unsafe_caller_request_ids_are_replaced(bad: str) -> None:
    resp = _client().post("/api/items", json={"blob": "a"}, headers={"X-Request-ID": bad})
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"].startswith("nex-")
    assert resp.headers["X-Nexus-Correlation-ID"] == resp.headers["X-Request-ID"]


def test_telemetry_middleware_is_plain_asgi() -> None:
    from starlette.middleware.base import BaseHTTPMiddleware

    assert not issubclass(NexusTelemetryMiddleware, BaseHTTPMiddleware)
