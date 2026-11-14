"""Nexus API: security response headers and static asset cache rules.

``NexusSecurityHeadersMiddleware`` adds a Content Security Policy, HSTS, ``X-Content-Type-Options``,
``X-Frame-Options``, ``Referrer-Policy`` and ``Permissions-Policy`` to every HTTP response, and
optionally sets cache headers for static files:

* responses under ``immutable_prefixes`` (for example content hashed ``/assets/``) with status 200
  get ``Cache-Control: public, max-age=31536000, immutable``;
* HTML responses get ``Cache-Control: no-cache`` so a new deploy is picked up immediately.

Headers the application already set are left alone. It is plain ASGI middleware, so streaming
responses (SSE, downloads) are not buffered.
"""

from __future__ import annotations

from dataclasses import dataclass

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

DEFAULT_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; "
    "form-action 'self'; frame-ancestors 'none'"
)

# FastAPI's Swagger UI (/docs) loads its bundle from jsdelivr and boots with an inline script.
SWAGGER_UI_CSP = (
    "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; connect-src 'self'; object-src 'none'; "
    "base-uri 'self'; frame-ancestors 'none'"
)

IMMUTABLE_CACHE = "public, max-age=31536000, immutable"
NO_CACHE = "no-cache"


@dataclass(frozen=True)
class SecurityHeadersConfig:
    """Which headers to send. Set a field to None (or False) to omit that header."""

    content_security_policy: str | None = DEFAULT_CSP
    # (path prefix, policy) pairs; the longest matching prefix wins over the default policy.
    csp_overrides: tuple[tuple[str, str], ...] = (("/docs", SWAGGER_UI_CSP),)
    strict_transport_security: str | None = "max-age=31536000"
    content_type_options: bool = True
    frame_options: str | None = "DENY"
    referrer_policy: str | None = "same-origin"
    permissions_policy: str | None = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    immutable_prefixes: tuple[str, ...] = ()
    html_no_cache: bool = True

    def csp_for(self, path: str) -> str | None:
        best: tuple[int, str] | None = None
        for prefix, policy in self.csp_overrides:
            if path.startswith(prefix) and (best is None or len(prefix) > best[0]):
                best = (len(prefix), policy)
        return best[1] if best else self.content_security_policy


class NexusSecurityHeadersMiddleware:
    """ASGI middleware that applies a ``SecurityHeadersConfig`` to every HTTP response."""

    def __init__(self, app: ASGIApp, config: SecurityHeadersConfig | None = None) -> None:
        self.app = app
        self.config = config or SecurityHeadersConfig()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        cfg = self.config

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                csp = cfg.csp_for(path)
                if csp:
                    headers.setdefault("Content-Security-Policy", csp)
                if cfg.strict_transport_security:
                    headers.setdefault("Strict-Transport-Security", cfg.strict_transport_security)
                if cfg.content_type_options:
                    headers.setdefault("X-Content-Type-Options", "nosniff")
                if cfg.frame_options:
                    headers.setdefault("X-Frame-Options", cfg.frame_options)
                if cfg.referrer_policy:
                    headers.setdefault("Referrer-Policy", cfg.referrer_policy)
                if cfg.permissions_policy:
                    headers.setdefault("Permissions-Policy", cfg.permissions_policy)

                if "cache-control" not in headers:
                    status = int(message.get("status", 200))
                    if status == 200 and any(path.startswith(p) for p in cfg.immutable_prefixes):
                        headers["Cache-Control"] = IMMUTABLE_CACHE
                    elif cfg.html_no_cache and headers.get("content-type", "").startswith("text/html"):
                        headers["Cache-Control"] = NO_CACHE
            await send(message)

        await self.app(scope, receive, send_with_headers)
