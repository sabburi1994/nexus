"""Nexus AI package: Vertex AI & Gemini 3.8 client, pricing, and structured output."""
from nexus.ai.client import GeminiClient, GeminiResponse, get_gcp_access_token, get_gcp_project
from nexus.ai.pricing import DEFAULT_MODEL, calculate_cost_usd

__all__ = [
    "GeminiClient",
    "GeminiResponse",
    "calculate_cost_usd",
    "DEFAULT_MODEL",
    "get_gcp_access_token",
    "get_gcp_project",
]
