"""Nexus API: in-process rate limiting (sliding window), as a route dependency or as middleware.

State lives in memory per process. On Cloud Run every instance counts on its own, so with
``max_instance_count = 2`` the effective ceiling is at most twice each limit; use a shared store
when a limit must be exact across instances.

Two ways to use it:

* per route: ``@app.post("/api/v1/scan", dependencies=[Depends(rate_limit(limiter))])``
* app wide by path: ``app.add_middleware(RateLimitMiddleware, rules=[RateLimitRule(...)])``

A limited request gets HTTP 429 with ``Retry-After`` and the Nexus error body
``{"error": "rate_limited", "message": ..., "retry_after": seconds}``.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from fastapi import HTTPException, Request
from starlette.types import ASGIApp, Receive, Scope, Send

RATE_LIMITED_MESSAGE = "Too many requests. Wait a moment and try again."


class SlidingWindowLimiter:
    """At most ``limit`` hits per ``window_seconds`` per key, tracking at most ``max_keys`` keys."""

    def __init__(self, limit: int, window_seconds: float, max_keys: int = 10_000) -> None:
        if limit < 1 or window_seconds <= 0:
            raise ValueError("limit must be >= 1 and window_seconds > 0")
        self.limit = limit
        self.window = window_seconds
        self.max_keys = max_keys
        self._hits: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    def hit(self, key: str, now: float | None = None) -> float | None:
        """Record a request. Returns None when allowed, else the seconds until a slot frees up."""
        ts = time.monotonic() if now is None else now
        with self._lock:
            bucket = self._hits.get(key)
            if bucket is None:
                bucket = deque()
                self._hits[key] = bucket
            self._hits.move_to_end(key)
            while bucket and ts - bucket[0] >= self.window:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return max(1.0, self.window - (ts - bucket[0]))
            bucket.append(ts)
            while len(self._hits) > self.max_keys:
                self._hits.popitem(last=False)
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def client_ip(request: Request, trusted_proxy_hops: int = 0) -> str:
    """The caller's address, trusting ``X-Forwarded-For`` only for ``trusted_proxy_hops`` proxies.

    Cloud Run's front end appends the real client address as the last entry, so use 1 there and
    0 (ignore the header, which callers can forge) when nothing trusted sits in front.
    """
    if trusted_proxy_hops > 0:
        forwarded = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
        if len(forwarded) >= trusted_proxy_hops:
            return forwarded[-trusted_proxy_hops]
    return request.client.host if request.client else "unknown"


def hashed(value: str) -> str:
    """Short stable digest, so credentials used in a key are never kept in memory as is."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


KeyFunc = Callable[[Request], str]


def ip_key(trusted_proxy_hops: int = 0) -> KeyFunc:
    """Key by client address."""
    return lambda request: client_ip(request, trusted_proxy_hops)


def ip_and_credential_key(trusted_proxy_hops: int = 0) -> KeyFunc:
    """Key by client address plus a hash of the Authorization header, so signed in users behind one
    address (an office, a proxy) each get their own budget."""

    def key(request: Request) -> str:
        ip = client_ip(request, trusted_proxy_hops)
        authorization = request.headers.get("authorization")
        return f"{ip}|{hashed(authorization)}" if authorization else ip

    return key


class RateLimitExceeded(HTTPException):
    """429 raised by ``rate_limit``; ``create_nexus_app`` renders it as the Nexus error body."""

    def __init__(self, retry_after: float, message: str = RATE_LIMITED_MESSAGE) -> None:
        self.retry_after = int(retry_after + 0.999)
        self.message = message
        super().__init__(
            status_code=429,
            detail={"error": "rate_limited", "message": message, "retry_after": self.retry_after},
            headers={"Retry-After": str(self.retry_after)},
        )

    def body(self) -> dict[str, object]:
        return {"error": "rate_limited", "message": self.message, "retry_after": self.retry_after}


def rate_limit(
    limiter: SlidingWindowLimiter,
    key: KeyFunc | None = None,
    *,
    global_limiter: SlidingWindowLimiter | None = None,
) -> Callable[[Request], None]:
    """FastAPI dependency enforcing ``limiter`` per key (client address by default).

    ``global_limiter`` adds one shared budget for every caller of the route (for example to cap
    an expensive endpoint per instance).
    """
    key_func = key or ip_key()

    def dependency(request: Request) -> None:
        retry = limiter.hit(key_func(request))
        if retry is None and global_limiter is not None:
            retry = global_limiter.hit("*")
        if retry is not None:
            raise RateLimitExceeded(retry)

    return dependency


@dataclass(frozen=True)
class RateLimitRule:
    """A limiter applied to requests whose path starts with one of ``path_prefixes``.

    Empty ``methods`` means every method except OPTIONS (CORS preflight is never limited).
    """

    limiter: SlidingWindowLimiter
    path_prefixes: tuple[str, ...] = ("/",)
    methods: frozenset[str] = field(default_factory=frozenset)

    def matches(self, method: str, path: str) -> bool:
        if method == "OPTIONS":
            return False
        if self.methods and method not in self.methods:
            return False
        return any(path.startswith(p) for p in self.path_prefixes)


class RateLimitMiddleware:
    """ASGI middleware applying the first matching ``RateLimitRule`` to each HTTP request.

    Put specific rules (``POST /api/auth/``) before general ones (``/``). Paths in ``exempt``
    (health checks by default) are never limited.
    """

    def __init__(
        self,
        app: ASGIApp,
        rules: Iterable[RateLimitRule],
        key: KeyFunc | None = None,
        exempt: Iterable[str] = ("/health", "/ready", "/healthz"),
        enabled: bool = True,
    ) -> None:
        self.app = app
        self.rules = list(rules)
        self.key = key or ip_key()
        self.exempt = tuple(exempt)
        self.enabled = enabled

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return
        path: str = scope.get("path", "")
        method: str = scope.get("method", "GET")
        if path in self.exempt:
            await self.app(scope, receive, send)
            return
        rule = next((r for r in self.rules if r.matches(method, path)), None)
        if rule is not None:
            retry = rule.limiter.hit(self.key(Request(scope)))
            if retry is not None:
                exc = RateLimitExceeded(retry)
                body = json.dumps(exc.body()).encode("utf-8")
                await send(
                    {
                        "type": "http.response.start",
                        "status": 429,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(body)).encode()),
                            (b"retry-after", str(exc.retry_after).encode()),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": body})
                return
        await self.app(scope, receive, send)
