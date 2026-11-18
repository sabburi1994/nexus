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
    """Vertex AI global list price: 0.75 / 3.75 USD per million until 2026-12-31, 1.50 / 7.50 from 2027."""
    import datetime

    intro = datetime.date(2026, 11, 17)
    standard = datetime.date(2027, 1, 1)
    # 1M input + 1M output
    assert round(calculate_cost_usd(1_000_000, 1_000_000, model="gemini-3.8-flash", on=intro), 4) == 4.5
    assert round(calculate_cost_usd(1_000_000, 1_000_000, model="gemini-3.8-flash", on=standard), 4) == 9.0
    assert round(calculate_cost_usd(1_000_000, 0, model="gemini-3.8-flash", on=datetime.date(2026, 12, 31)), 4) == 0.75

    # 10,000 input, 2,000 output
    cost_small = calculate_cost_usd(10_000, 2_000, model="gemini-3.8-flash", on=intro)
    expected = (10_000 / 1e6 * 0.75) + (2_000 / 1e6 * 3.75)
    assert abs(cost_small - expected) < 1e-9


def test_unknown_models_are_priced_high_so_caps_never_undercount() -> None:
    from nexus.ai.pricing import FALLBACK_PRICE, price_per_million

    assert price_per_million("some-future-model") == FALLBACK_PRICE
    assert price_per_million("models/gemini-3.8-flash@001") != FALLBACK_PRICE


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


def test_nexus_api_cors_closed_by_default() -> None:
    """With no origins configured no CORS headers are emitted."""
    client = TestClient(create_nexus_app(title="TestApp"))
    resp = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in resp.headers
    pre = client.options(
        "/health",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in pre.headers


def test_nexus_api_cors_explicit_origins_allow_credentials() -> None:
    client = TestClient(create_nexus_app(title="TestApp", cors_origins=["https://app.example.com"]))
    ok = client.get("/health", headers={"Origin": "https://app.example.com"})
    assert ok.headers["access-control-allow-origin"] == "https://app.example.com"
    assert ok.headers["access-control-allow-credentials"] == "true"
    other = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in other.headers


def test_nexus_api_cors_wildcard_never_sends_credentials() -> None:
    client = TestClient(create_nexus_app(title="TestApp", cors_origins=["*"]))
    resp = client.get("/health", headers={"Origin": "https://any.example"})
    assert resp.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in resp.headers
    with pytest.raises(ValueError):
        create_nexus_app(title="TestApp", cors_origins=["*"], cors_allow_credentials=True)


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
    client = GeminiClient(project_id="example-project")

    class MockResponse:
        status_code = 200

        def json(self) -> dict[str, Any]:
            return {
                "candidates": [{"content": {"parts": [{"text": "Gemini 3.8 Flash operational."}]}}],
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


def test_mcp_server_exposes_stage1_to_3_tools(tmp_path: Path) -> None:
    """Verify embedded MCP server exposes Stage 1-3 tools and executes them."""
    from nexus.cli.main import build_mcp_server

    sample_file = tmp_path / "models.py"
    sample_file.write_text('API_KEY = "sk-demo9876543210abcdef9876543210"\n', encoding="utf-8")

    server = build_mcp_server()
    tools_resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tool_names = {t["name"] for t in tools_resp["result"]["tools"]}
    assert {"nexus_check_ai", "nexus_audit", "nexus_blast_radius", "nexus_guardrail", "nexus_roi"} <= tool_names

    audit_resp = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "nexus_audit", "arguments": {"path": str(tmp_path)}},
        }
    )
    assert audit_resp["result"]["isError"] is False
    assert "SECRET_LEAK" in audit_resp["result"]["content"][0]["text"]


def test_gemini_client_explicit_api_key_precedence() -> None:
    """Explicit api_key argument must prefer direct Gemini API over ambient GCP metadata."""
    client = GeminiClient(api_key="AIza-test-explicit-key")
    url, headers = client._build_url_and_headers("gemini-3.8-flash")
    assert "generativelanguage.googleapis.com" in url
    # The key must travel in a header, never in the URL (URLs end up in logs and tracebacks).
    assert "AIza-test-explicit-key" not in url
    assert headers == {"Content-Type": "application/json", "x-goog-api-key": "AIza-test-explicit-key"}


def test_get_gcp_project_raises_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """No project configured must raise a clear configuration error, never fall back to a hard coded project."""
    from nexus.ai import NexusConfigurationError, get_gcp_project

    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.setattr("nexus.ai.client.shutil.which", lambda name: None)
    with pytest.raises(NexusConfigurationError, match="GCP_PROJECT_ID"):
        get_gcp_project()


def test_get_gcp_project_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from nexus.ai import get_gcp_project

    monkeypatch.setenv("GCP_PROJECT_ID", "example-project")
    assert get_gcp_project() == "example-project"


def test_vertex_path_without_project_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A Vertex AI call with a token but no project and no API key fails with a configuration error."""
    from nexus.ai import NexusConfigurationError
    from nexus.ai import client as ai_client

    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr("nexus.ai.client.shutil.which", lambda name: None)
    monkeypatch.setattr(ai_client, "get_gcp_access_token", lambda: "ya29.test-token")
    client = GeminiClient()
    assert client.project_id is None
    with pytest.raises(NexusConfigurationError):
        client._build_url_and_headers("gemini-3.8-flash")
