"""Pytest suite for Nexus Showcase API."""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["healthy"] is True
    assert "Nexus Showcase API" in data["app"]


def test_scan_and_list_reports() -> None:
    # 1. Trigger scan
    payload = {"target": "Semiconductor Supply Chain", "sector": "Technology"}
    resp = client.post("/api/v1/scan", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["target"] == "Semiconductor Supply Chain"
    assert data["model"] == "gemini-3.8-flash"
    assert "id" in data

    # 2. Verify stored in reports
    resp_list = client.get("/api/v1/reports")
    assert resp_list.status_code == 200
    reports = resp_list.json()
    assert len(reports) >= 1
    assert any(r["id"] == data["id"] for r in reports)
