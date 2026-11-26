"""Offline unit tests for pluggable HTTP model providers and create_provider()."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import BaseModel

from nexus.agents.context import AgentContext
from nexus.ai.client import NexusConfigurationError
from nexus.cli.main import dream_cmd
from nexus.providers import (
    AnthropicProvider,
    BudgetedProvider,
    MockProvider,
    OpenAICompatibleProvider,
    VertexAIProvider,
    create_provider,
)


class _SummarySchema(BaseModel):
    title: str
    score: int


def _mock_client(handler: Any) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_openai_compatible_generate_structured_and_converse() -> None:
    seen: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://api.openai.com/v1/chat/completions")
        assert request.headers["authorization"] == "Bearer sk-test-openai-key"
        body = json.loads(request.content.decode("utf-8"))
        seen.append(body)

        if body.get("response_format", {}).get("type") == "json_object":
            content = '```json\n{"title": "WatchHub", "score": 98}\n```'
        elif "tools" in body:
            content = "Using tool"
        else:
            content = "Hello from OpenAI"

        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-1",
                "choices": [{"message": {"role": "assistant", "content": content}}],
                "usage": {"prompt_tokens": 1000, "completion_tokens": 500},
            },
        )

    provider = OpenAICompatibleProvider(
        api_key="sk-test-openai-key",
        default_model="gpt-4o-mini",
        http_client=_mock_client(handler),
    )

    resp = provider.generate("Ping", system_instruction="Be brief")
    assert resp.text == "Hello from OpenAI"
    assert resp.input_tokens == 1000
    assert resp.output_tokens == 500
    assert resp.cost_usd > 0.0
    assert seen[0]["messages"][0] == {"role": "system", "content": "Be brief"}

    ctx = AgentContext(max_budget_usd=5.0)
    budgeted = BudgetedProvider(provider, ctx)
    parsed = budgeted.structured("Summarize", _SummarySchema, system_instruction="Strict JSON")
    assert parsed == _SummarySchema(title="WatchHub", score=98)
    assert budgeted.last_usage is not None
    assert budgeted.last_usage.input_tokens == 1000
    assert ctx.accumulated_cost_usd > 0.0

    conv = provider.converse(
        messages=[{"role": "user", "content": "Check status"}],
        tools=[{"type": "function", "function": {"name": "ping", "parameters": {"type": "object"}}}],
    )
    assert conv.text == "Using tool"
    assert "tools" in seen[2]


def test_openai_compatible_ollama_zero_cost_and_error_redaction() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ConnectError("transient drop", request=request)
        if calls == 2:
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"role": "assistant", "content": "local reply"}}],
                    "usage": {"prompt_tokens": 400, "completion_tokens": 200},
                },
            )
        return httpx.Response(401, text="invalid key sk-secret1234567890abcdef1234567890")

    provider = OpenAICompatibleProvider(
        api_key="ollama",
        base_url="http://127.0.0.1:11434/v1",
        default_model="llama3.1",
        provider_name="ollama",
        zero_cost=True,
        max_retries=2,
        http_client=_mock_client(handler),
    )
    ok = provider.generate("Hi")
    assert ok.text == "local reply"
    assert ok.cost_usd == 0.0
    assert calls == 2

    with pytest.raises(RuntimeError) as exc_info:
        provider.generate("Fail")
    assert "sk-secret1234567890abcdef1234567890" not in str(exc_info.value)
    assert "[REDACTED_API_KEY]" in str(exc_info.value)


def test_anthropic_generate_structured_tool_use_and_converse() -> None:
    seen: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://api.anthropic.com/v1/messages")
        assert request.headers["x-api-key"] == "sk-ant-test-key"
        assert request.headers["anthropic-version"] == "2023-06-01"
        body = json.loads(request.content.decode("utf-8"))
        seen.append(body)

        if "tool_choice" in body:
            content: list[dict[str, Any]] = [
                {
                    "type": "tool_use",
                    "id": "tu_1",
                    "name": "emit_structured_output",
                    "input": {"title": "FinHub", "score": 95},
                }
            ]
        else:
            content = [{"type": "text", "text": "Hello from Claude"}]

        return httpx.Response(
            200,
            json={
                "id": "msg_1",
                "content": content,
                "usage": {"input_tokens": 800, "output_tokens": 300},
            },
        )

    provider = AnthropicProvider(
        api_key="sk-ant-test-key",
        default_model="claude-sonnet-4-5",
        http_client=_mock_client(handler),
    )

    resp = provider.generate("Ping", system_instruction="Be concise")
    assert resp.text == "Hello from Claude"
    assert resp.input_tokens == 800
    assert resp.output_tokens == 300
    assert resp.cost_usd > 0.0
    assert seen[0]["system"] == "Be concise"

    ctx = AgentContext(max_budget_usd=5.0)
    budgeted = BudgetedProvider(provider, ctx)
    parsed = budgeted.structured("Extract", _SummarySchema)
    assert parsed == _SummarySchema(title="FinHub", score=95)
    assert budgeted.last_usage is not None
    assert budgeted.last_usage.output_tokens == 300
    assert ctx.accumulated_cost_usd > 0.0

    conv = provider.converse(
        messages=[{"role": "user", "content": "Run tool"}],
        tools=[{"name": "audit", "description": "Audit repo", "input_schema": {"type": "object"}}],
    )
    assert conv.text == "Hello from Claude"
    assert seen[2]["tools"][0]["name"] == "audit"


def test_anthropic_error_redaction_and_missing_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(NexusConfigurationError):
        OpenAICompatibleProvider()
    with pytest.raises(NexusConfigurationError):
        AnthropicProvider()

    def fail_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="rejected token sk-ant-api03-1234567890abcdef1234567890")

    provider = AnthropicProvider(api_key="sk-ant-ok", http_client=_mock_client(fail_handler))
    with pytest.raises(RuntimeError) as exc_info:
        provider.generate("test")
    assert "sk-ant-api03-1234567890abcdef1234567890" not in str(exc_info.value)


def test_create_provider_factory_and_dream_cmd_mock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-openai")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env")

    assert isinstance(create_provider("vertex"), VertexAIProvider)
    assert isinstance(create_provider("gemini"), VertexAIProvider)
    assert isinstance(create_provider("openai"), OpenAICompatibleProvider)
    assert isinstance(create_provider("anthropic"), AnthropicProvider)
    assert isinstance(create_provider("claude"), AnthropicProvider)
    ollama = create_provider("ollama")
    assert isinstance(ollama, OpenAICompatibleProvider)
    assert ollama.name == "ollama"
    assert ollama.zero_cost is True
    assert isinstance(create_provider("mock"), MockProvider)

    with pytest.raises(ValueError, match="Unknown provider"):
        create_provider("does-not-exist")

    # End-to-end dream_cmd using --provider mock (zero network / zero spend)
    dream_cmd("A simple invoice tracker", output_dir=tmp_path, run_tests=False, provider_name="mock")
    assert any(tmp_path.iterdir())
