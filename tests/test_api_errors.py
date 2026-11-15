"""Unhandled errors must not leak exception text to clients; they are logged with the request id."""

from __future__ import annotations

import logging

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from nexus.api import create_nexus_app
from nexus.api.app import INTERNAL_ERROR_MESSAGE

SECRET_DETAIL = "SELECT password FROM users WHERE id=1; /srv/app/db.py; token=sk-live-123"


def _client() -> TestClient:
    app = create_nexus_app(title="ErrApp")

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError(SECRET_DETAIL)

    @app.get("/teapot")
    async def teapot() -> None:
        raise HTTPException(status_code=418, detail="I am a teapot")

    # Starlette re-raises after the handler ran; a real server only logs it. Mirror the server.
    return TestClient(app, raise_server_exceptions=False)


def test_unhandled_error_returns_generic_message_and_request_id(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="nexus.api")
    resp = _client().get("/boom")
    assert resp.status_code == 500
    body = resp.json()
    assert body == {
        "error": "internal_server_error",
        "message": INTERNAL_ERROR_MESSAGE,
        "request_id": body["request_id"],
    }
    assert body["request_id"].startswith("nex-")
    assert resp.headers["X-Request-ID"] == body["request_id"]
    for leak in ("SELECT", "password", "/srv/app", "sk-live", "RuntimeError"):
        assert leak not in resp.text


def test_unhandled_error_is_logged_server_side_with_the_request_id(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="nexus.api")
    resp = _client().get("/boom", headers={"X-Request-ID": "req-abc-123"})
    assert resp.json()["request_id"] == "req-abc-123"
    records = [r for r in caplog.records if r.name == "nexus.api"]
    assert records, "the exception must be logged"
    record = records[0]
    assert "req-abc-123" in record.getMessage()
    assert "RuntimeError" in record.getMessage()
    assert record.exc_info is not None and SECRET_DETAIL in str(record.exc_info[1])


def test_http_exceptions_keep_their_status_and_detail() -> None:
    resp = _client().get("/teapot")
    assert resp.status_code == 418
    assert resp.json() == {"detail": "I am a teapot"}
