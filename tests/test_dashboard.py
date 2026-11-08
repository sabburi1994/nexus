"""Tests for the Nexus Localhost Visualizer and Telemetry Dashboard."""
from __future__ import annotations

import pytest
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
    """Verify dashboard serves HTML and status endpoints."""
    app = create_dashboard_app()
    client = TestClient(app)

    # Status
    status_resp = client.get("/api/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] in ("online", "listening")

    # Events
    events_resp = client.get("/api/events")
    assert events_resp.status_code == 200
    assert isinstance(events_resp.json(), list)

    # HTML UI
    ui_resp = client.get("/")
    assert ui_resp.status_code == 200
    assert "Nexus Squad Visualizer" in ui_resp.text
    assert "EventSource" in ui_resp.text
