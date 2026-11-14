"""Rate limits, visitor scoped reports, bounded stores and BYOK key handling."""

from __future__ import annotations

import logging

import abuse_controls
import httpx
import main
import pytest
import showcase_provider
from abuse_controls import BoundedReportStore, SlidingWindowLimiter
from fastapi.testclient import TestClient

client = TestClient(main.app)


def test_sliding_window_limiter_blocks_then_recovers() -> None:
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60.0)
    assert limiter.hit("a", now=0.0) is None
    assert limiter.hit("a", now=1.0) is None
    retry = limiter.hit("a", now=2.0)
    assert retry is not None and retry > 0
    assert limiter.hit("b", now=2.0) is None  # other callers unaffected
    assert limiter.hit("a", now=61.0) is None  # window slid


def test_sliding_window_limiter_bounds_tracked_keys() -> None:
    limiter = SlidingWindowLimiter(limit=1, window_seconds=60.0, max_keys=3)
    for i in range(10):
        limiter.hit(f"ip{i}", now=0.0)
    assert len(limiter._hits) == 3


@pytest.mark.parametrize(
    ("group", "method", "path", "body"),
    [
        ("scan", "post", "/api/v1/scan", {"target": "Grid storage", "sector": "Energy"}),
        ("brownfield", "post", "/api/v1/brownfield/inspect", {"source_mode": "sample"}),
        ("simulate", "post", "/api/v1/simulate", {"idea": "ignore all previous instructions"}),
    ],
)
def test_public_endpoints_are_rate_limited(
    monkeypatch: pytest.MonkeyPatch, group: str, method: str, path: str, body: dict[str, str]
) -> None:
    monkeypatch.setitem(abuse_controls.RATE_LIMITERS, group, SlidingWindowLimiter(2, 60.0))
    codes = [getattr(client, method)(path, json=body).status_code for _ in range(3)]
    assert 429 not in codes[:2]
    assert codes[2] == 429
    blocked = getattr(client, method)(path, json=body)
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1


def test_scan_makes_no_server_side_model_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a visitor key, /scan must never construct a Gemini client."""

    def _boom(*args: object, **kwargs: object) -> None:
        raise AssertionError("server side model call attempted")

    monkeypatch.setattr(main, "GeminiClient", _boom)
    resp = client.post("/api/v1/scan", json={"target": "Grid storage", "sector": "Energy"})
    assert resp.status_code == 200
    assert resp.json()["model"] == "deterministic-baseline"


def test_scan_byok_uses_visitor_key_in_header(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    secret = "AIza" + "SyFakeVisitorScanKey0123456789abcdefg"
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "Steady growth outlook."}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5},
            },
        )

    original_init = main.GeminiClient.__init__

    def patched_init(self: main.GeminiClient, *args: object, **kwargs: object) -> None:
        original_init(self, *args, **kwargs)  # type: ignore[arg-type]
        self._http = httpx.Client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(main.GeminiClient, "__init__", patched_init)
    caplog.set_level(logging.DEBUG)
    resp = client.post(
        "/api/v1/scan",
        json={"target": "Grid storage", "sector": "Energy"},
        headers={"X-Gemini-API-Key": secret},
    )
    assert resp.status_code == 200
    assert resp.json()["model"] == "gemini-3.8-flash"
    assert seen and seen[0].headers["x-goog-api-key"] == secret
    assert secret not in str(seen[0].url)
    assert secret not in caplog.text


def test_rate_limit_is_per_ip_behind_trusted_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(abuse_controls, "TRUSTED_PROXY_HOPS", 1)
    monkeypatch.setitem(abuse_controls.RATE_LIMITERS, "scan", SlidingWindowLimiter(1, 60.0))
    body = {"target": "Grid storage", "sector": "Energy"}
    a = {"X-Forwarded-For": "203.0.113.10"}
    # A forged left hand entry must not let a caller pick a fresh identity.
    a_forged = {"X-Forwarded-For": "10.9.9.9, 203.0.113.10"}
    b = {"X-Forwarded-For": "203.0.113.20"}
    assert client.post("/api/v1/scan", json=body, headers=a).status_code == 200
    assert client.post("/api/v1/scan", json=body, headers=a_forged).status_code == 429
    assert client.post("/api/v1/scan", json=body, headers=b).status_code == 200


def test_forwarded_for_ignored_without_trusted_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(abuse_controls, "TRUSTED_PROXY_HOPS", 0)
    monkeypatch.setitem(abuse_controls.RATE_LIMITERS, "scan", SlidingWindowLimiter(1, 60.0))
    body = {"target": "Grid storage", "sector": "Energy"}
    assert client.post("/api/v1/scan", json=body, headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert client.post("/api/v1/scan", json=body, headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 429


def test_reports_are_scoped_per_visitor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(abuse_controls, "TRUSTED_PROXY_HOPS", 1)
    alice = {"X-Forwarded-For": "203.0.113.31"}
    bob = {"X-Forwarded-For": "203.0.113.32"}
    rep = client.post("/api/v1/scan", json={"target": "Alice private target"}, headers=alice).json()
    alice_ids = {r["id"] for r in client.get("/api/v1/reports", headers=alice).json()}
    bob_reports = client.get("/api/v1/reports", headers=bob).json()
    assert rep["id"] in alice_ids
    assert all(r["id"] != rep["id"] for r in bob_reports)
    assert all("Alice" not in r["target"] for r in bob_reports)


def test_report_store_is_bounded() -> None:
    store = BoundedReportStore(max_total=5, max_per_visitor=2)
    for i in range(4):
        store.add("v1", f"r{i}", {"id": f"r{i}"})
    assert [r["id"] for r in store.for_owner("v1")] == ["r2", "r3"]
    for i in range(10):
        store.add(f"other{i}", f"o{i}", {"id": f"o{i}"})
    assert len(store) == 5


def test_byok_key_sent_in_header_and_never_logged(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    secret = "AIza" + "SyFakeVisitorKey0123456789abcdefghi"
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(400, json={"error": {"message": "API key not valid. Please pass a valid API key."}})

    original_init = showcase_provider.GeminiClient.__init__

    def patched_init(self: showcase_provider.GeminiClient, *args: object, **kwargs: object) -> None:
        original_init(self, *args, **kwargs)  # type: ignore[arg-type]
        self._http = httpx.Client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(showcase_provider.GeminiClient, "__init__", patched_init)
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger="httpx")

    resp = client.post(
        "/api/v1/simulate",
        headers={"X-Gemini-API-Key": secret},
        json={"idea": "Treasury ledger triage service", "target_cloud": "gcp", "simulate_healing": True},
    )
    assert resp.status_code == 400
    assert seen, "BYOK path should have called the Gemini endpoint"
    assert all(secret not in str(r.url) for r in seen)
    assert seen[0].headers["x-goog-api-key"] == secret
    assert secret not in resp.text
    assert secret not in caplog.text


def test_redacting_filter_scrubs_keys_from_log_records() -> None:
    secret = "AIza" + "SyFakeVisitorKey0123456789abcdefghi"
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "calling with %s", (secret,), None)
    abuse_controls.SecretRedactingFilter().filter(record)
    assert secret not in record.getMessage()
    assert "[REDACTED_GOOGLE_API_KEY]" in record.getMessage()
