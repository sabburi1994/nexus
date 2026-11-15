"""Abuse controls for the public showcase API: per IP rate limits, visitor scoping, log redaction.

State is in memory per Cloud Run instance. With ``max_instance_count = 3`` the effective
ceiling is at most three times each limit, which is acceptable for a demo; a shared store
(Memorystore, Firestore) would be needed for exact global limits.
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import threading
from collections import OrderedDict
from collections.abc import Callable

from fastapi import Request

from nexus.api.ratelimit import RateLimitExceeded, SlidingWindowLimiter
from nexus.api.ratelimit import client_ip as _nexus_client_ip
from nexus.security import sanitize_text

__all__ = ["RATE_LIMITERS", "TRUSTED_PROXY_HOPS", "SlidingWindowLimiter", "client_ip", "rate_limit", "visitor_id"]


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


# Number of trusted reverse proxies that append to X-Forwarded-For. Cloud Run's front end
# appends the real client address as the last entry, so 1 is right on Cloud Run (K_SERVICE set)
# and 0 (ignore the header, which callers can forge) everywhere else.
TRUSTED_PROXY_HOPS = _env_int("SHOWCASE_TRUSTED_PROXY_HOPS", 1 if os.getenv("K_SERVICE") else 0)

# Per process salt: visitor ids are stable for an instance's lifetime but are not raw IPs.
_VISITOR_SALT = secrets.token_bytes(16)


def client_ip(request: Request) -> str:
    """Best estimate of the caller's address, trusting only ``TRUSTED_PROXY_HOPS`` proxies."""
    return _nexus_client_ip(request, TRUSTED_PROXY_HOPS)


def visitor_id(request: Request) -> str:
    """Opaque per visitor id (salted hash of the client address)."""
    return hashlib.sha256(_VISITOR_SALT + client_ip(request).encode("utf-8")).hexdigest()[:16]


# Per IP limits per instance (nexus.api.ratelimit). The showcase makes no server side model calls
# (only visitor supplied keys), so these protect CPU and memory rather than model spend.
RATE_LIMITERS: dict[str, SlidingWindowLimiter] = {
    "scan": SlidingWindowLimiter(_env_int("SHOWCASE_SCAN_PER_MINUTE", 5), 60.0),
    "simulate": SlidingWindowLimiter(_env_int("SHOWCASE_SIMULATE_PER_MINUTE", 6), 60.0),
    "brownfield": SlidingWindowLimiter(_env_int("SHOWCASE_BROWNFIELD_PER_MINUTE", 20), 60.0),
    "download": SlidingWindowLimiter(_env_int("SHOWCASE_DOWNLOAD_PER_MINUTE", 30), 60.0),
}


def rate_limit(group: str, global_group: str | None = None) -> Callable[[Request], None]:
    """FastAPI dependency enforcing the per IP limiter ``group`` (and an optional global one).

    Limiters are looked up at request time so tests can swap them. A limited request raises
    ``RateLimitExceeded``, which ``create_nexus_app`` renders as the Nexus 429 error body.
    """

    def _dependency(request: Request) -> None:
        retry = RATE_LIMITERS[group].hit(client_ip(request))
        if retry is None and global_group is not None:
            retry = RATE_LIMITERS[global_group].hit("*")
        if retry is not None:
            raise RateLimitExceeded(retry, "Rate limit exceeded for this demo endpoint; please retry shortly.")

    return _dependency


class BoundedReportStore:
    """Scan reports kept per visitor, capped in total and per visitor (oldest evicted first)."""

    def __init__(self, max_total: int = 500, max_per_visitor: int = 20) -> None:
        self.max_total = max_total
        self.max_per_visitor = max_per_visitor
        self._items: OrderedDict[str, tuple[str, dict[str, object]]] = OrderedDict()
        self._lock = threading.Lock()

    def add(self, owner: str, report_id: str, report: dict[str, object]) -> None:
        with self._lock:
            self._items[report_id] = (owner, report)
            owned = [rid for rid, (o, _) in self._items.items() if o == owner]
            for rid in owned[: max(0, len(owned) - self.max_per_visitor)]:
                del self._items[rid]
            while len(self._items) > self.max_total:
                self._items.popitem(last=False)

    def for_owner(self, owner: str) -> list[dict[str, object]]:
        with self._lock:
            return [report for o, report in self._items.values() if o == owner]

    def __len__(self) -> int:
        return len(self._items)


class SecretRedactingFilter(logging.Filter):
    """Logging filter that runs every record through the Nexus secret sanitizer."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True
        cleaned = sanitize_text(message)
        if cleaned != message:
            record.msg = cleaned
            record.args = None
        return True


def install_log_redaction() -> None:
    """Keep BYOK keys and other credentials out of logs.

    The Gemini key is sent in a request header (never the URL), httpx request logging is
    turned down, and every handler known at start up redacts known credential formats.
    """
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    redactor = SecretRedactingFilter()
    for name in (None, "uvicorn", "uvicorn.error", "uvicorn.access", "nexus", "nexus.ai"):
        logger = logging.getLogger(name)
        if not any(isinstance(f, SecretRedactingFilter) for f in logger.filters):
            logger.addFilter(redactor)
        for handler in logger.handlers:
            if not any(isinstance(f, SecretRedactingFilter) for f in handler.filters):
                handler.addFilter(redactor)
