"""Nexus Providers: Factory helper for constructing providers by name."""

from __future__ import annotations

from nexus.ai.pricing import DEFAULT_MODEL
from nexus.providers.anthropic import DEFAULT_ANTHROPIC_MODEL, AnthropicProvider
from nexus.providers.base import BaseModelProvider
from nexus.providers.mock import MockProvider
from nexus.providers.openai_compat import (
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OPENAI_MODEL,
    OpenAICompatibleProvider,
)
from nexus.providers.vertex import VertexAIProvider

SUPPORTED_PROVIDERS: tuple[str, ...] = ("vertex", "gemini", "openai", "anthropic", "claude", "ollama", "mock")


def create_provider(
    provider: str = "vertex",
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    project_id: str | None = None,
) -> BaseModelProvider:
    """Create a ``BaseModelProvider`` by short name.

    Supported names: ``vertex`` (alias ``gemini``), ``openai``, ``anthropic`` (alias ``claude``),
    ``ollama`` (local OpenAI-compatible server, zero cost), and ``mock``.
    """
    key = provider.strip().lower()
    if key in ("vertex", "gemini"):
        return VertexAIProvider(
            project_id=project_id,
            default_model=model or DEFAULT_MODEL,
            api_key=api_key,
        )
    if key == "openai":
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=base_url,
            default_model=model or DEFAULT_OPENAI_MODEL,
            provider_name="openai",
        )
    if key == "ollama":
        return OpenAICompatibleProvider(
            api_key=api_key or "ollama",
            base_url=base_url or DEFAULT_OLLAMA_BASE_URL,
            default_model=model or DEFAULT_OLLAMA_MODEL,
            provider_name="ollama",
            zero_cost=True,
        )
    if key in ("anthropic", "claude"):
        return AnthropicProvider(
            api_key=api_key,
            base_url=base_url,
            default_model=model or DEFAULT_ANTHROPIC_MODEL,
        )
    if key == "mock":
        return MockProvider()
    raise ValueError(f"Unknown provider {provider!r}. Choose one of: {', '.join(SUPPORTED_PROVIDERS)}.")
