"""Nexus API package: Application factory and middleware."""

from nexus.ai.client import GeminiClient
from nexus.api.app import configure_cors, create_nexus_app
from nexus.api.middleware import NexusTelemetryMiddleware
from nexus.api.security_headers import NexusSecurityHeadersMiddleware, SecurityHeadersConfig
from nexus.db.base import Base, NexusEntity

__all__ = [
    "Base",
    "GeminiClient",
    "NexusEntity",
    "NexusSecurityHeadersMiddleware",
    "NexusTelemetryMiddleware",
    "SecurityHeadersConfig",
    "configure_cors",
    "create_nexus_app",
]
