"""Nexus API package: Application factory and middleware."""

from nexus.ai.client import GeminiClient
from nexus.api.app import create_nexus_app
from nexus.api.middleware import NexusTelemetryMiddleware
from nexus.db.base import Base, NexusEntity

__all__ = [
    "Base",
    "GeminiClient",
    "NexusEntity",
    "NexusTelemetryMiddleware",
    "create_nexus_app",
]
