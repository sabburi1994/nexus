"""Tests for NexusSecurityHeadersMiddleware and create_nexus_app(security_headers=...)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from fastapi.testclient import TestClient

from nexus.api import SecurityHeadersConfig, create_nexus_app
from nexus.api.security_headers import DEFAULT_CSP, IMMUTABLE_CACHE, SWAGGER_UI_CSP


def _app(config: SecurityHeadersConfig | bool) -> TestClient:
    app = create_nexus_app(title="HeadersApp", security_headers=config)

    @app.get("/page", response_class=HTMLResponse)
    async def page() -> str:
        return "<html><body>hi</body></html>"

    @app.get("/assets/app-abc123.js", response_class=PlainTextResponse)
    async def asset() -> str:
        return "console.log(1)"

    @app.get("/custom")
    async def custom() -> PlainTextResponse:
        return PlainTextResponse("x", headers={"X-Frame-Options": "SAMEORIGIN", "Cache-Control": "private"})

    @app.get("/stream")
    async def stream() -> StreamingResponse:
        async def gen() -> AsyncIterator[bytes]:
            yield b"a"
            yield b"b"

        return StreamingResponse(gen(), media_type="text/plain")

    return TestClient(app)


def test_security_headers_off_by_default() -> None:
    client = TestClient(create_nexus_app(title="Plain"))
    resp = client.get("/health")
    assert "content-security-policy" not in resp.headers
    assert "x-frame-options" not in resp.headers


def test_default_security_headers() -> None:
    client = _app(True)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers["content-security-policy"] == DEFAULT_CSP
    assert resp.headers["strict-transport-security"] == "max-age=31536000"
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "same-origin"
    assert "camera=()" in resp.headers["permissions-policy"]
    assert "frame-ancestors 'none'" in DEFAULT_CSP and "object-src 'none'" in DEFAULT_CSP


def test_html_is_no_cache_and_hashed_assets_are_immutable() -> None:
    client = _app(SecurityHeadersConfig(immutable_prefixes=("/assets/",)))
    assert client.get("/page").headers["cache-control"] == "no-cache"
    assert client.get("/assets/app-abc123.js").headers["cache-control"] == IMMUTABLE_CACHE
    missing = client.get("/assets/missing.js")
    assert missing.status_code == 404
    assert missing.headers.get("cache-control") != IMMUTABLE_CACHE
    assert "cache-control" not in client.get("/health").headers  # JSON API responses untouched


def test_app_set_headers_are_kept() -> None:
    resp = _app(True).get("/custom")
    assert resp.headers["x-frame-options"] == "SAMEORIGIN"
    assert resp.headers["cache-control"] == "private"
    assert resp.headers["x-content-type-options"] == "nosniff"


def test_docs_get_swagger_policy_and_overrides_pick_longest_prefix() -> None:
    client = _app(True)
    assert client.get("/docs").headers["content-security-policy"] == SWAGGER_UI_CSP
    cfg = SecurityHeadersConfig(csp_overrides=(("/a", "A"), ("/a/b", "AB")))
    assert cfg.csp_for("/a/b/c") == "AB"
    assert cfg.csp_for("/a/x") == "A"
    assert cfg.csp_for("/z") == DEFAULT_CSP


def test_streaming_responses_get_headers() -> None:
    resp = _app(True).get("/stream")
    assert resp.text == "ab"
    assert resp.headers["x-content-type-options"] == "nosniff"


def test_disabling_individual_headers() -> None:
    client = _app(SecurityHeadersConfig(content_security_policy=None, csp_overrides=(), strict_transport_security=None))
    resp = client.get("/health")
    assert "content-security-policy" not in resp.headers
    assert "strict-transport-security" not in resp.headers
    assert resp.headers["x-frame-options"] == "DENY"


def test_health_and_ready_accept_head() -> None:
    client = _app(True)
    for path in ("/health", "/ready"):
        resp = client.head(path)
        assert resp.status_code == 200
        assert resp.content == b""
