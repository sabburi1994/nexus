"""Nexus API package: application factory, middleware and the backend adoption kit."""

from nexus.ai.client import GeminiClient
from nexus.api.app import configure_cors, create_nexus_app
from nexus.api.middleware import NexusTelemetryMiddleware
from nexus.api.oidc import GoogleOidcVerifier, OidcRefused, require_google_oidc
from nexus.api.ratelimit import (
    RateLimitExceeded,
    RateLimitMiddleware,
    RateLimitRule,
    SlidingWindowLimiter,
    client_ip,
    ip_and_credential_key,
    ip_key,
    rate_limit,
)
from nexus.api.security_headers import NexusSecurityHeadersMiddleware, SecurityHeadersConfig
from nexus.api.spa import mount_spa, resolve_inside
from nexus.db.base import Base, NexusEntity

__all__ = [
    "Base",
    "GeminiClient",
    "GoogleOidcVerifier",
    "NexusEntity",
    "NexusSecurityHeadersMiddleware",
    "NexusTelemetryMiddleware",
    "OidcRefused",
    "RateLimitExceeded",
    "RateLimitMiddleware",
    "RateLimitRule",
    "SecurityHeadersConfig",
    "SlidingWindowLimiter",
    "client_ip",
    "configure_cors",
    "create_nexus_app",
    "ip_and_credential_key",
    "ip_key",
    "mount_spa",
    "rate_limit",
    "require_google_oidc",
    "resolve_inside",
]
