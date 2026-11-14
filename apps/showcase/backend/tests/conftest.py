"""Shared fixtures: keep the showcase test suite offline and isolated from rate limit state."""

from __future__ import annotations

from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _offline_and_fresh_limits(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    import abuse_controls

    def _no_vertex() -> None:
        raise AssertionError("tests must never fetch Google Cloud credentials")

    # Never reach a real Google Cloud project (or the developer's gcloud credentials) from tests.
    monkeypatch.setattr("nexus.ai.client.get_gcp_access_token", _no_vertex)
    for name, limiter in list(abuse_controls.RATE_LIMITERS.items()):
        monkeypatch.setitem(
            abuse_controls.RATE_LIMITERS,
            name,
            abuse_controls.SlidingWindowLimiter(limiter.limit, limiter.window, limiter.max_keys),
        )
    yield
