"""Nexus AI package: Vertex AI & Gemini 3.8 client, pricing, and structured output."""

from nexus.ai.client import (
    GeminiClient,
    GeminiResponse,
    NexusConfigurationError,
    find_gcp_project,
    get_gcp_access_token,
    get_gcp_project,
)
from nexus.ai.pricing import DEFAULT_MODEL, calculate_cost_usd

__all__ = [
    "DEFAULT_MODEL",
    "GeminiClient",
    "GeminiResponse",
    "NexusConfigurationError",
    "calculate_cost_usd",
    "find_gcp_project",
    "get_gcp_access_token",
    "get_gcp_project",
]
