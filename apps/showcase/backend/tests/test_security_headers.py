"""The showcase serves the standard security headers and cache rules through Nexus's middleware."""

from __future__ import annotations

import re
from pathlib import Path

import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

STATIC = Path(main.__file__).resolve().parent / "static"


def _hashed_asset() -> str:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    match = re.search(r'src="(/assets/[^"]+\.js)"', html)
    assert match, "index.html should reference a hashed JS bundle"
    return match.group(1)


def _assert_security_headers(headers: object) -> None:
    h = dict(headers)  # type: ignore[call-overload]
    csp = h["content-security-policy"]
    for directive in (
        "default-src 'self'",
        "script-src 'self';",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
        "img-src 'self' data: blob:",
    ):
        assert directive in csp
    assert "unsafe-eval" not in csp
    assert h["strict-transport-security"] == "max-age=31536000"
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"
    assert h["referrer-policy"] == "same-origin"


def test_head_root_returns_200_with_headers() -> None:
    resp = client.head("/")
    assert resp.status_code == 200
    assert resp.content == b""
    _assert_security_headers(resp.headers)
    assert resp.headers["cache-control"] == "no-cache"


def test_index_html_no_cache_and_csp_allows_only_google_fonts_extra() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    _assert_security_headers(resp.headers)
    assert resp.headers["cache-control"] == "no-cache"
    csp = resp.headers["content-security-policy"]
    assert "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;" in csp
    assert "font-src 'self' https://fonts.gstatic.com;" in csp
    # Every external origin the page references must be allowed, and nothing more.
    external = set(re.findall(r'(?:href|src)="(https://[^/"]+)', resp.text))
    assert external <= {"https://fonts.googleapis.com", "https://fonts.gstatic.com"}
    assert "<script>" not in resp.text  # no inline scripts, so script-src 'self' is enough


def test_hashed_assets_are_immutable() -> None:
    resp = client.get(_hashed_asset())
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "public, max-age=31536000, immutable"
    _assert_security_headers(resp.headers)


def test_api_responses_carry_headers_without_cache_rules() -> None:
    resp = client.get("/api/v1/framework-health")
    assert resp.status_code == 200
    _assert_security_headers(resp.headers)
    assert "cache-control" not in resp.headers


def test_head_health() -> None:
    assert client.head("/health").status_code == 200
