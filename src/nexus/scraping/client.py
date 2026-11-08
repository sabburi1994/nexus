"""Nexus Scraping: Resilient web scraping and ingestion client."""
from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any
import httpx

logger = logging.getLogger("nexus.scraping")

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
]


class ScraperClient:
    """Resilient HTTP client for scraping with rate limiting, retries, and headers."""

    def __init__(
        self,
        rate_limit_delay_seconds: float = 1.0,
        max_retries: int = 3,
        timeout: float = 30.0,
        user_agents: list[str] | None = None,
    ) -> None:
        self.rate_limit_delay = rate_limit_delay_seconds
        self.max_retries = max_retries
        self.timeout = timeout
        self.user_agents = user_agents or DEFAULT_USER_AGENTS
        self._last_request_time = 0.0
        self._client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)

    def _get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
        }

    async def _rate_limit(self) -> None:
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    async def fetch(self, url: str, **kwargs: Any) -> str:
        """Fetch content from a URL with retries and exponential backoff."""
        headers = self._get_headers()
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            await self._rate_limit()
            try:
                resp = await self._client.get(url, headers=headers, **kwargs)
                if resp.status_code == 200:
                    return resp.text
                if resp.status_code in (429, 500, 502, 503, 504):
                    logger.warning("Scrape retry %d for %s (status %d)", attempt, url, resp.status_code)
                    await asyncio.sleep(2.0 ** attempt)
                    continue
                resp.raise_for_status()
            except Exception as exc:
                last_error = exc
                logger.warning("Scrape error on attempt %d for %s: %s", attempt, url, exc)
                await asyncio.sleep(2.0 ** attempt)

        raise RuntimeError(f"Failed to fetch {url} after {self.max_retries} attempts: {last_error}")

    async def close(self) -> None:
        """Close underlying HTTP client."""
        await self._client.aclose()
