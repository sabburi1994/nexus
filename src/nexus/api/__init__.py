"""Nexus API package: Application factory and middleware."""
from nexus.api.app import create_nexus_app
from nexus.api.middleware import NexusTelemetryMiddleware
from nexus.db.base import Base, NexusEntity
from nexus.ai.client import GeminiClient

__all__ = [
    "create_nexus_app",
    "NexusTelemetryMiddleware",
    "NexusEntity",
    "Base",
    "GeminiClient",
]
