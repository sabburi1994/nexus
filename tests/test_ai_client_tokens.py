"""Access token caching and the 401 retry of nexus.ai.client (found by the real model benchmark).

The first real benchmark lost three ideas to HTTP 401 after 39 minutes: a token was reused for a
flat 40 minutes from when Nexus fetched it, although gcloud and the metadata server can hand out a
token that is already partly used, and a 401 was never retried.
"""

from __future__ import annotations

import subprocess
from typing import Any

import httpx
import pytest

from nexus.ai import client as ai_client


@pytest.fixture(autouse=True)
def _clean_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    ai_client.invalidate_gcp_access_token()
    monkeypatch.delenv("GCP_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GOOGLE_OAUTH_ACCESS_TOKEN", raising=False)


def _clock(monkeypatch: pytest.MonkeyPatch, start: float = 1_000_000.0) -> list[float]:
    now = [start]
    monkeypatch.setattr("nexus.ai.client.time.time", lambda: now[0])
    return now


def test_metadata_token_is_reused_until_shortly_before_it_expires(monkeypatch: pytest.MonkeyPatch) -> None:
    now = _clock(monkeypatch)
    issued: list[str] = []

    def metadata(url: str, **_: Any) -> httpx.Response:
        issued.append(f"meta-{len(issued)}")
        # The metadata server can return a token with only 10 minutes left.
        return httpx.Response(200, json={"access_token": issued[-1], "expires_in": 600})

    monkeypatch.setattr("nexus.ai.client.httpx.get", metadata)
    assert ai_client.get_gcp_access_token() == "meta-0"
    now[0] += 240  # 4 minutes later: still valid for 6, margin is 5
    assert ai_client.get_gcp_access_token() == "meta-0"
    now[0] += 120  # 6 minutes after issue: inside the 5 minute margin, refresh
    assert ai_client.get_gcp_access_token() == "meta-1"


def test_gcloud_token_is_reused_for_five_minutes_only(monkeypatch: pytest.MonkeyPatch) -> None:
    now = _clock(monkeypatch)
    monkeypatch.setattr("nexus.ai.client.httpx.get", lambda *a, **k: (_ for _ in ()).throw(httpx.ConnectError("no")))
    monkeypatch.setattr("nexus.ai.client.shutil.which", lambda name: "gcloud")
    calls: list[int] = []

    def gcloud(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(1)
        return subprocess.CompletedProcess(args, 0, stdout=f"ya29.token-{len(calls)}\n", stderr="")

    monkeypatch.setattr("nexus.ai.client.subprocess.run", gcloud)
    assert ai_client.get_gcp_access_token() == "ya29.token-1"
    now[0] += 299
    assert ai_client.get_gcp_access_token() == "ya29.token-1"
    now[0] += 2
    assert ai_client.get_gcp_access_token() == "ya29.token-2"


def test_a_401_refreshes_the_token_and_retries_once(monkeypatch: pytest.MonkeyPatch) -> None:
    tokens = iter(["ya29.stale", "ya29.fresh", "ya29.never"])
    monkeypatch.setattr(ai_client, "get_gcp_access_token", lambda: next(tokens))
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["Authorization"])
        if request.headers["Authorization"] == "Bearer ya29.stale":
            return httpx.Response(401, json={"error": {"code": 401}})
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "ok"}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "thoughtsTokenCount": 7},
            },
        )

    client = ai_client.GeminiClient(project_id="demo-project")
    client._http = httpx.Client(transport=httpx.MockTransport(handler))
    res = client.generate("hi")
    assert res.text == "ok"
    assert seen == ["Bearer ya29.stale", "Bearer ya29.fresh"]
    assert res.output_tokens == 12  # thinking tokens are billed as output


def test_dropped_connections_are_retried_then_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ai_client, "get_gcp_access_token", lambda: "ya29.ok")
    monkeypatch.setattr("time.sleep", lambda s: None)
    failures = [httpx.RemoteProtocolError("Server disconnected"), httpx.ConnectError("getaddrinfo failed")]

    def handler(request: httpx.Request) -> httpx.Response:
        if failures:
            raise failures.pop(0)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "back"}]}}]})

    client = ai_client.GeminiClient(project_id="demo-project")
    client._http = httpx.Client(transport=httpx.MockTransport(handler))
    assert client.generate("hi").text == "back"

    def always_down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("getaddrinfo failed")

    client._http = httpx.Client(transport=httpx.MockTransport(always_down))
    with pytest.raises(httpx.ConnectError):
        client.generate("hi")


def test_a_second_401_is_returned_not_retried_forever(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ai_client, "get_gcp_access_token", lambda: "ya29.revoked")
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(401, json={"error": {"code": 401}})

    client = ai_client.GeminiClient(project_id="demo-project")
    client._http = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(RuntimeError, match="401"):
        client.generate("hi")
    assert len(calls) == 2
