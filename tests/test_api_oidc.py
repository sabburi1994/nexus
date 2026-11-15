"""nexus.api.oidc: Google signed OIDC ID tokens (Cloud Scheduler, service account callers)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

jwt = pytest.importorskip("jwt")
rsa = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.rsa")

from nexus.api.oidc import GOOGLE_CERTS_URL, GoogleOidcVerifier, OidcRefused, require_google_oidc  # noqa: E402

AUDIENCE = "https://app.example.test/internal/tick"
CALLER = "scheduler-invoker@example-project.iam.gserviceaccount.com"
NOW = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)


def _keypair(kid: str) -> tuple[Any, dict[str, Any]]:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private.public_key()))
    jwk.update({"kid": kid, "alg": "RS256", "use": "sig"})
    return private, jwk


KEY, JWK = _keypair("k1")
OTHER_KEY, OTHER_JWK = _keypair("k2")


def _token(**overrides: Any) -> str:
    claims: dict[str, Any] = {
        "aud": AUDIENCE,
        "iss": "https://accounts.google.com",
        "email": CALLER,
        "email_verified": True,
        "iat": int((NOW - timedelta(minutes=1)).timestamp()),
        "exp": int((NOW + timedelta(minutes=59)).timestamp()),
        "sub": "1234567890",
    }
    key = overrides.pop("_key", KEY)
    kid = overrides.pop("_kid", "k1")
    claims.update(overrides)
    for name in [k for k, v in claims.items() if v is None]:
        del claims[name]
    return str(jwt.encode(claims, key, algorithm="RS256", headers={"kid": kid}))


class Certs:
    """Counts fetches of Google's key set; can fail on demand."""

    def __init__(self, keys: list[dict[str, Any]] | None = None, status: int = 200) -> None:
        self.keys = keys if keys is not None else [JWK]
        self.status = status
        self.calls = 0

    def handler(self, request: httpx.Request) -> httpx.Response:
        assert str(request.url) == GOOGLE_CERTS_URL
        self.calls += 1
        if self.status != 200:
            return httpx.Response(self.status)
        return httpx.Response(200, json={"keys": self.keys})


def _verifier(certs: Certs, clock: list[datetime] | None = None, callers: Any = CALLER) -> GoogleOidcVerifier:
    now = clock or [NOW]
    transport = httpx.MockTransport(certs.handler)
    return GoogleOidcVerifier(
        AUDIENCE,
        callers,
        clock=lambda: now[0],
        http=httpx.Client(transport=transport),
        async_http=httpx.AsyncClient(transport=transport),
    )


def test_valid_token_returns_claims_sync_and_async() -> None:
    certs = Certs()
    verifier = _verifier(certs)
    claims = verifier.verify(f"Bearer {_token()}")
    assert claims["email"] == CALLER
    import asyncio

    assert asyncio.run(verifier.averify(f"bearer {_token()}"))["aud"] == AUDIENCE
    assert certs.calls == 1  # keys cached


@pytest.mark.parametrize(
    ("authorization", "status"),
    [(None, 401), ("", 401), ("Basic abc", 401), ("Bearer ", 401), ("Bearer not.a.jwt", 401)],
)
def test_missing_or_malformed_bearer_is_401(authorization: str | None, status: int) -> None:
    with pytest.raises(OidcRefused) as refused:
        _verifier(Certs()).verify(authorization)
    assert refused.value.status == status


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"aud": "https://other.example.test"}, "rejected"),
        ({"iss": "https://evil.example.test"}, "rejected"),
        ({"email": "someone-else@example-project.iam.gserviceaccount.com"}, "another account"),
        ({"email_verified": False}, "not verified"),
        ({"email_verified": None}, "not verified"),
        ({"exp": int((NOW - timedelta(minutes=5)).timestamp())}, "expired"),
        ({"iat": int((NOW + timedelta(minutes=5)).timestamp())}, "future"),
        ({"email": None}, "rejected"),
        ({"_key": OTHER_KEY}, "rejected"),
    ],
)
def test_wrong_tokens_are_403(overrides: dict[str, Any], reason: str) -> None:
    with pytest.raises(OidcRefused) as refused:
        _verifier(Certs()).verify(f"Bearer {_token(**overrides)}")
    assert refused.value.status == 403
    assert reason in refused.value.reason


def test_clock_skew_tolerates_two_minutes() -> None:
    just_expired = _token(exp=int((NOW - timedelta(seconds=90)).timestamp()))
    assert _verifier(Certs()).verify(f"Bearer {just_expired}")["email"] == CALLER


def test_non_rs256_token_is_refused() -> None:
    hs = jwt.encode({"aud": AUDIENCE, "email": CALLER}, "shared-secret", algorithm="HS256", headers={"kid": "k1"})
    with pytest.raises(OidcRefused) as refused:
        _verifier(Certs()).verify(f"Bearer {hs}")
    assert refused.value.status == 403 and "RS256" in refused.value.reason


def test_unknown_key_triggers_one_refresh_then_refuses_or_accepts() -> None:
    certs = Certs([JWK])
    verifier = _verifier(certs)
    verifier.verify(f"Bearer {_token()}")
    with pytest.raises(OidcRefused):
        verifier.verify(f"Bearer {_token(_key=OTHER_KEY, _kid='k2')}")
    assert certs.calls == 2
    certs.keys = [JWK, OTHER_JWK]  # Google rotated keys
    assert verifier.verify(f"Bearer {_token(_key=OTHER_KEY, _kid='k2')}")["email"] == CALLER
    assert certs.calls == 3


def test_keys_are_refetched_after_their_ttl() -> None:
    certs = Certs()
    clock = [NOW]
    verifier = _verifier(certs, clock)
    verifier.verify(f"Bearer {_token()}")
    clock[0] = NOW + timedelta(minutes=30)
    verifier.verify(
        f"Bearer {_token(iat=int((clock[0] - timedelta(minutes=1)).timestamp()), exp=int((clock[0] + timedelta(minutes=30)).timestamp()))}"
    )
    assert certs.calls == 1
    clock[0] = NOW + timedelta(hours=2)
    later = _token(
        iat=int((clock[0] - timedelta(minutes=1)).timestamp()), exp=int((clock[0] + timedelta(minutes=30)).timestamp())
    )
    verifier.verify(f"Bearer {later}")
    assert certs.calls == 2


def test_key_endpoint_failure_is_503() -> None:
    with pytest.raises(OidcRefused) as refused:
        _verifier(Certs(status=500)).verify(f"Bearer {_token()}")
    assert refused.value.status == 503


def test_several_callers_and_settings_helper() -> None:
    other = "ops-runner@example-project.iam.gserviceaccount.com"
    verifier = _verifier(Certs(), callers=[other, CALLER.upper()])
    assert verifier.verify(f"Bearer {_token()}")["email"] == CALLER
    assert GoogleOidcVerifier.from_settings("", CALLER) is None
    assert GoogleOidcVerifier.from_settings(AUDIENCE, "") is None
    built = GoogleOidcVerifier.from_settings(AUDIENCE, f"{CALLER}, {other}")
    assert built is not None and built.callers == (CALLER, other)
    with pytest.raises(ValueError):
        GoogleOidcVerifier("", CALLER)


def _app(source: Any) -> TestClient:
    app = FastAPI()

    @app.post("/internal/tick")
    async def tick(claims: dict[str, Any] = Depends(require_google_oidc(source))) -> dict[str, str]:
        return {"caller": claims["email"]}

    return TestClient(app)


def test_dependency_maps_refusals_and_hides_the_reason(caplog: pytest.LogCaptureFixture) -> None:
    client = _app(_verifier(Certs()))
    assert client.post("/internal/tick", headers={"Authorization": f"Bearer {_token()}"}).json() == {"caller": CALLER}
    assert client.post("/internal/tick").status_code == 401
    wrong = client.post("/internal/tick", headers={"Authorization": f"Bearer {_token(email='x@example.test')}"})
    assert wrong.status_code == 403 and wrong.json() == {"detail": "Not allowed"}
    assert "another account" in caplog.text


def test_dependency_is_404_when_not_configured_and_reads_app_state() -> None:
    assert _app(None).post("/internal/tick").status_code == 404
    verifier = _verifier(Certs())
    client = _app(lambda request: getattr(request.app.state, "ops_verifier", None))
    assert client.post("/internal/tick").status_code == 404
    client.app.state.ops_verifier = verifier  # type: ignore[attr-defined]
    ok = client.post("/internal/tick", headers={"Authorization": f"Bearer {_token()}"})
    assert ok.status_code == 200
