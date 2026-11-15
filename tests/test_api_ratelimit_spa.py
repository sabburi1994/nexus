"""nexus.api.ratelimit and nexus.api.spa."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from nexus.api import (
    RateLimitMiddleware,
    RateLimitRule,
    SlidingWindowLimiter,
    create_nexus_app,
    ip_and_credential_key,
    ip_key,
    mount_spa,
    rate_limit,
    resolve_inside,
)
from nexus.api.spa import IMMUTABLE, NO_CACHE

# Rate limiting ----------------------------------------------------------------------------------


def test_sliding_window_blocks_then_recovers_and_bounds_keys() -> None:
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60.0, max_keys=3)
    assert limiter.hit("a", now=0.0) is None
    assert limiter.hit("a", now=1.0) is None
    retry = limiter.hit("a", now=2.0)
    assert retry is not None and 57.0 < retry <= 60.0
    assert limiter.hit("b", now=2.0) is None
    assert limiter.hit("a", now=61.0) is None
    for i in range(10):
        limiter.hit(f"ip{i}", now=70.0)
    assert len(limiter._hits) == 3
    with pytest.raises(ValueError):
        SlidingWindowLimiter(limit=0, window_seconds=60)


def _limited_app(limiter: SlidingWindowLimiter, hops: int = 0) -> TestClient:
    app = create_nexus_app(title="RL")

    @app.post("/api/scan", dependencies=[Depends(rate_limit(limiter, ip_key(hops)))])
    async def scan() -> dict[str, str]:
        return {"ok": "yes"}

    return TestClient(app)


def test_route_dependency_returns_the_nexus_429_body() -> None:
    client = _limited_app(SlidingWindowLimiter(2, 60.0))
    assert [client.post("/api/scan").status_code for _ in range(2)] == [200, 200]
    resp = client.post("/api/scan", headers={"X-Request-ID": "req-1"})
    assert resp.status_code == 429
    body = resp.json()
    assert body["error"] == "rate_limited" and body["request_id"] == "req-1"
    assert body["retry_after"] >= 1 and resp.headers["Retry-After"] == str(body["retry_after"])
    assert "message" in body


def test_forwarded_for_is_trusted_only_for_configured_hops() -> None:
    trusting = _limited_app(SlidingWindowLimiter(1, 60.0), hops=1)
    assert trusting.post("/api/scan", headers={"X-Forwarded-For": "203.0.113.1"}).status_code == 200
    # A forged left hand entry does not give a fresh identity: the last hop is the client.
    assert trusting.post("/api/scan", headers={"X-Forwarded-For": "9.9.9.9, 203.0.113.1"}).status_code == 429
    assert trusting.post("/api/scan", headers={"X-Forwarded-For": "203.0.113.2"}).status_code == 200

    ignoring = _limited_app(SlidingWindowLimiter(1, 60.0), hops=0)
    assert ignoring.post("/api/scan", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert ignoring.post("/api/scan", headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 429


def test_global_limiter_caps_all_callers() -> None:
    app = create_nexus_app(title="RL")
    per_ip, shared = SlidingWindowLimiter(10, 60.0), SlidingWindowLimiter(2, 60.0)

    @app.get("/expensive", dependencies=[Depends(rate_limit(per_ip, ip_key(1), global_limiter=shared))])
    async def expensive() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)
    codes = [client.get("/expensive", headers={"X-Forwarded-For": f"198.51.100.{i}"}).status_code for i in range(3)]
    assert codes == [200, 200, 429]


def test_credential_key_hashes_the_authorization_header() -> None:
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"authorization", b"Bearer secret-token-123")],
        "client": ("203.0.113.9", 1234),
    }
    key = ip_and_credential_key()(Request(scope))
    assert key.startswith("203.0.113.9|") and "secret-token-123" not in key


def test_middleware_applies_first_matching_rule_and_skips_health_and_preflight() -> None:
    app = create_nexus_app(title="RL")
    auth = SlidingWindowLimiter(1, 60.0)
    general = SlidingWindowLimiter(3, 60.0)
    app.add_middleware(
        RateLimitMiddleware,
        rules=[
            RateLimitRule(auth, ("/api/auth/",), frozenset({"POST"})),
            RateLimitRule(general, ("/api/",)),
        ],
    )

    @app.post("/api/auth/login")
    async def login() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/api/items")
    async def items() -> list[int]:
        return [1]

    client = TestClient(app)
    assert client.post("/api/auth/login").status_code == 200
    blocked = client.post("/api/auth/login")
    assert blocked.status_code == 429 and blocked.json()["error"] == "rate_limited"
    assert int(blocked.headers["Retry-After"]) >= 1
    assert [client.get("/api/items").status_code for _ in range(4)] == [200, 200, 200, 429]
    assert all(client.get("/health").status_code == 200 for _ in range(10))
    assert client.options("/api/items").status_code != 429


# SPA mount --------------------------------------------------------------------------------------


@pytest.fixture()
def dist(tmp_path: Path) -> Path:
    root = tmp_path / "dist"
    (root / "assets").mkdir(parents=True)
    (root / "index.html").write_text("<!doctype html><div id=root></div>", encoding="utf-8")
    (root / "assets" / "index-abc123.js").write_text("console.log(1)", encoding="utf-8")
    (root / "assets" / "index-abc123.css").write_text("body{}", encoding="utf-8")
    (root / "sw.js").write_text("self.addEventListener('fetch',()=>{})", encoding="utf-8")
    (root / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("TOP SECRET", encoding="utf-8")
    return root


def _spa_client(dist: Path) -> TestClient:
    app = create_nexus_app(title="SPA")

    @app.get("/api/items")
    async def items() -> list[int]:
        return [1, 2]

    mount_spa(app, dist)
    return TestClient(app)


def test_spa_serves_assets_immutable_and_index_no_cache(dist: Path) -> None:
    client = _spa_client(dist)
    js = client.get("/assets/index-abc123.js")
    assert js.status_code == 200 and js.headers["cache-control"] == IMMUTABLE
    assert js.headers["content-type"].startswith("text/javascript")
    assert client.get("/assets/index-abc123.css").headers["content-type"].startswith("text/css")
    for path in ("/", "/today", "/money/accounts/42"):
        page = client.get(path)
        assert page.status_code == 200 and "id=root" in page.text
        assert page.headers["cache-control"] == NO_CACHE
    assert client.get("/sw.js").headers["cache-control"] == NO_CACHE
    assert client.get("/favicon.svg").headers["content-type"] == "image/svg+xml"
    assert client.head("/").status_code == 200


def test_spa_keeps_api_routes_and_404s_unknown_api_paths(dist: Path) -> None:
    client = _spa_client(dist)
    assert client.get("/api/items").json() == [1, 2]
    missing = client.get("/api/nope")
    assert missing.status_code == 404 and missing.headers["content-type"].startswith("application/json")
    assert client.get("/health").json()["status"] == "ok"
    # A stale page asking for an old hashed asset gets 404, never index.html.
    assert client.get("/assets/index-old999.js").status_code == 404


@pytest.mark.parametrize(
    "path", ["/../secret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt", "/..%2fsecret.txt"]
)
def test_spa_never_serves_files_outside_dist(dist: Path, path: str) -> None:
    resp = _spa_client(dist).get(path)
    assert "TOP SECRET" not in resp.text


def test_resolve_inside_rejects_escapes_and_nul(dist: Path) -> None:
    assert resolve_inside(dist, "index.html") == (dist / "index.html").resolve()
    for bad in ("../secret.txt", "/../../secret.txt", "a\0b", "", "assets"):
        assert resolve_inside(dist, bad) is None


def test_spa_without_a_build_answers_404_instead_of_failing(tmp_path: Path) -> None:
    app = create_nexus_app(title="SPA")
    mount_spa(app, tmp_path / "missing")
    resp = TestClient(app).get("/")
    assert resp.status_code == 404
