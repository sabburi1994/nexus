"""Unit tests for the Nexus Platform Framework."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from nexus.ai.client import GeminiClient
from nexus.ai.pricing import calculate_cost_usd
from nexus.api.app import create_nexus_app
from nexus.db.base import NexusEntity


def test_gemini_3_8_pricing() -> None:
    """Verify Gemini 3.8 pricing per million tokens ($0.075 / $0.30)."""
    # 1M input ($0.075) + 1M output ($0.30) = $0.375
    cost = calculate_cost_usd(1_000_000, 1_000_000, model="gemini-3.8-flash")
    assert round(cost, 4) == 0.375

    # 10,000 input, 2,000 output
    cost_small = calculate_cost_usd(10_000, 2_000, model="gemini-3.8-flash")
    expected = (10_000 / 1e6 * 0.075) + (2_000 / 1e6 * 0.30)
    assert abs(cost_small - expected) < 1e-7


def test_nexus_api_factory() -> None:
    """Verify create_nexus_app adds health endpoints and telemetry headers."""
    app = create_nexus_app(title="TestApp", version="1.0.0")
    client = TestClient(app)

    # Health check
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == "TestApp"
    assert "timestamp" in data

    # Telemetry headers
    assert "X-Request-ID" in resp.headers
    assert "X-Process-Time" in resp.headers


class ConcreteEntity(NexusEntity):
    __tablename__ = "test_entities"


def test_nexus_db_entity_metadata() -> None:
    """Verify NexusEntity defines required fields."""
    columns = ConcreteEntity.__table__.columns
    assert "id" in columns
    assert "created_at" in columns
    assert "updated_at" in columns


class SampleExtract(BaseModel):
    category: str
    confidence: float


def test_gemini_client_mock_generate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify GeminiClient generates response properly."""
    client = GeminiClient(project_id="finhub-510316")

    class MockResponse:
        status_code = 200

        def json(self) -> dict[str, Any]:
            return {
                "candidates": [
                    {"content": {"parts": [{"text": "Gemini 3.8 Flash operational."}]}}
                ],
                "usageMetadata": {
                    "promptTokenCount": 15,
                    "candidatesTokenCount": 8,
                },
            }

    monkeypatch.setattr(client, "_build_url_and_headers", lambda m: ("http://mock", {}))
    monkeypatch.setattr(client._http, "post", lambda *args, **kwargs: MockResponse())

    res = client.generate("Ping")
    assert res.text == "Gemini 3.8 Flash operational."
    assert res.input_tokens == 15
    assert res.output_tokens == 8
    assert res.cost_usd > 0


@pytest.mark.asyncio
async def test_scraper_client() -> None:
    """Verify ScraperClient initializes with standard headers."""
    from nexus.scraping.client import ScraperClient

    scraper = ScraperClient(rate_limit_delay_seconds=0.01)
    headers = scraper._get_headers()
    assert "User-Agent" in headers
    assert "Mozilla" in headers["User-Agent"]
    await scraper.close()


def test_cli_new_app(tmp_path: Path) -> None:
    """Verify nexus new command scaffolds an app structure."""
    from nexus.cli.main import scaffold_new_app

    test_dir = tmp_path / "apps"
    test_dir.mkdir(parents=True, exist_ok=True)
    scaffold_new_app(app_name="demo_service", output_dir=test_dir)

    assert (test_dir / "demo_service" / "pyproject.toml").exists()
    assert (test_dir / "demo_service" / "src" / "demo_service" / "main.py").exists()
    assert (test_dir / "demo_service" / "Dockerfile").exists()
