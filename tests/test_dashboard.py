"""Tests for the Nexus Localhost Visualizer and Telemetry Dashboard."""

from __future__ import annotations

from fastapi.testclient import TestClient

from nexus.dashboard.server import create_dashboard_app
from nexus.dashboard.telemetry import AgentEvent, EventType, event_bus


def test_event_bus_emission_and_history() -> None:
    """Verify event bus records events properly."""
    event = AgentEvent(
        event_type=EventType.AGENT_STARTED,
        agent_name="Business Analyst",
        message="Started requirements parsing",
        data={"user": "test"},
    )
    event_bus.emit(event)

    history = event_bus.get_history(limit=5)
    assert len(history) >= 1
    last = history[-1]
    assert last["agent_name"] == "Business Analyst"
    assert last["event_type"] == "agent_started"
    assert "Started requirements" in last["message"]


def test_dashboard_api_endpoints() -> None:
    """Verify dashboard serves offline HTML/CSS/JS, status, events, and security headers."""
    app = create_dashboard_app()
    client = TestClient(app)

    # Health route from create_nexus_app
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["healthy"] is True

    # Status
    status_resp = client.get("/api/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] in ("online", "listening")
    assert status_resp.headers["cache-control"] == "no-store"
    assert "x-request-id" in status_resp.headers

    # Events
    events_resp = client.get("/api/events")
    assert events_resp.status_code == 200
    assert isinstance(events_resp.json(), list)
    assert events_resp.headers["cache-control"] == "no-store"

    # HTML UI: offline, strict CSP, no external CDNs, no inline scripts or handlers
    ui_resp = client.get("/")
    assert ui_resp.status_code == 200
    assert "Nexus Squad Visualizer" in ui_resp.text
    assert "cdn.tailwindcss.com" not in ui_resp.text
    assert "https://" not in ui_resp.text
    assert "<script>" not in ui_resp.text
    assert "onclick=" not in ui_resp.text
    assert 'src="/dashboard.js"' in ui_resp.text
    assert 'href="/dashboard.css"' in ui_resp.text
    assert ui_resp.headers["cache-control"] == "no-cache"
    assert ui_resp.headers["x-content-type-options"] == "nosniff"
    assert ui_resp.headers["x-frame-options"] == "DENY"
    csp = ui_resp.headers["content-security-policy"]
    assert "script-src 'self';" in csp
    assert "style-src 'self';" in csp
    assert "unsafe-inline" not in csp

    # Bundled JS and CSS: same-origin, explicit media types, DOM-safe rendering (no innerHTML)
    js_resp = client.get("/dashboard.js")
    assert js_resp.status_code == 200
    assert "text/javascript" in js_resp.headers["content-type"]
    assert "EventSource" in js_resp.text
    assert "innerHTML" not in js_resp.text

    css_resp = client.get("/dashboard.css")
    assert css_resp.status_code == 200
    assert "text/css" in css_resp.headers["content-type"]
    assert "--nx-bg" in css_resp.text


def test_dashboard_cors_closed_by_default() -> None:
    """The telemetry API must not be readable cross-origin unless origins are configured."""
    client = TestClient(create_dashboard_app())
    resp = client.get("/api/events", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in resp.headers

    opened = TestClient(create_dashboard_app(cors_origins=["http://localhost:5173"]))
    ok = opened.get("/api/events", headers={"Origin": "http://localhost:5173"})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"
