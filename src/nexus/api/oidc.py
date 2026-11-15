"""Nexus API: verify Google signed OIDC ID tokens from Cloud Scheduler or service account callers.

Cloud Scheduler (and any Google service account) can call an HTTP endpoint with an OIDC ID token
for a chosen audience. ``GoogleOidcVerifier`` checks the token against Google's published keys
(RS256 signature), the expected audience, Google's issuer, expiry and issue time (with a small
clock skew), ``email_verified`` and the exact caller email(s). Anything else is refused:

* 401 when there is no usable bearer token,
* 403 for a token that is not from an allowed caller (bad signature, audience, issuer, time, email),
* 503 when Google's keys cannot be fetched.

The reason goes to the log only; clients get a generic detail. ``require_google_oidc`` turns a
verifier into a FastAPI dependency; when the app has no verifier configured (a laptop, a test
server) the route answers 404, as if it did not exist.

Needs the optional extra: ``pip install "nexus-agent-framework[oidc]"`` (PyJWT with crypto).
"""

from __future__ import annotations

import logging
import secrets
import threading
from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from fastapi import HTTPException, Request

logger = logging.getLogger("nexus.api.oidc")

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
DEFAULT_SKEW = timedelta(minutes=2)
DEFAULT_KEYS_TTL = timedelta(hours=1)


def _jwt() -> Any:
    try:
        import jwt  # PyJWT
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise ImportError(
            'GoogleOidcVerifier needs PyJWT with crypto: pip install "nexus-agent-framework[oidc]"'
        ) from exc
    return jwt


class OidcRefused(Exception):
    """The caller is not allowed. ``status`` is 401, 403 or 503; ``reason`` is for the log only."""

    def __init__(self, reason: str, status: int = 403) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status = status


class GoogleOidcVerifier:
    """Verifies ``Authorization: Bearer <Google ID token>`` for one audience and allowed callers.

    ``callers`` are service account emails (case insensitive). Keys are cached for ``keys_ttl``
    and refreshed early when a token names an unknown key id. ``clock`` and the HTTP clients are
    injectable for tests.
    """

    def __init__(
        self,
        audience: str,
        callers: str | Iterable[str],
        *,
        certs_url: str = GOOGLE_CERTS_URL,
        issuers: tuple[str, ...] = GOOGLE_ISSUERS,
        skew: timedelta = DEFAULT_SKEW,
        keys_ttl: timedelta = DEFAULT_KEYS_TTL,
        clock: Callable[[], datetime] | None = None,
        http: httpx.Client | None = None,
        async_http: httpx.AsyncClient | None = None,
    ) -> None:
        allowed = [callers] if isinstance(callers, str) else list(callers)
        self.callers = tuple(c.strip().lower() for c in allowed if c and c.strip())
        self.audience = audience.strip()
        if not self.audience or not self.callers:
            raise ValueError("an OIDC verifier needs an audience and at least one caller email")
        self.certs_url = certs_url
        self.issuers = issuers
        self.skew = skew
        self.keys_ttl = keys_ttl
        self.clock = clock or (lambda: datetime.now(UTC))
        self._http = http
        self._async_http = async_http
        self._keys: dict[str, Any] = {}
        self._keys_at: datetime | None = None
        self._lock = threading.Lock()

    @classmethod
    def from_settings(
        cls, audience: str | None, callers: str | Iterable[str] | None, **kwargs: Any
    ) -> GoogleOidcVerifier | None:
        """A verifier, or None when the audience or the callers are not configured.

        ``callers`` may be a comma separated string (an environment variable)."""
        if isinstance(callers, str):
            callers = [c for c in callers.split(",") if c.strip()]
        if not audience or not audience.strip() or not callers:
            return None
        return cls(audience, callers, **kwargs)

    # Keys -----------------------------------------------------------------------------------

    def _store_keys(self, payload: Any) -> None:
        jwt = _jwt()
        try:
            keys = {k["kid"]: jwt.PyJWK(k) for k in payload["keys"] if k.get("kid")}
        except (KeyError, TypeError, ValueError, jwt.PyJWTError) as exc:
            raise OidcRefused("signing keys are malformed", 503) from exc
        with self._lock:
            self._keys = keys
            self._keys_at = self.clock()

    def _needs_fetch(self, kid: str) -> bool:
        with self._lock:
            stale = self._keys_at is None or self.clock() - self._keys_at > self.keys_ttl
            return stale or kid not in self._keys

    def _cached_key(self, kid: str) -> Any:
        with self._lock:
            key = self._keys.get(kid)
        if key is None:
            raise OidcRefused("token signed with an unknown key")
        return key

    def _fetch_keys(self) -> None:
        client = self._http or httpx.Client(timeout=10.0)
        try:
            response = client.get(self.certs_url, timeout=10.0)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcRefused("signing keys are unavailable", 503) from exc
        finally:
            if self._http is None:
                client.close()
        self._store_keys(payload)

    async def _afetch_keys(self) -> None:
        client = self._async_http or httpx.AsyncClient(timeout=10.0)
        try:
            response = await client.get(self.certs_url, timeout=10.0)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcRefused("signing keys are unavailable", 503) from exc
        finally:
            if self._async_http is None:
                await client.aclose()
        self._store_keys(payload)

    # Verification ---------------------------------------------------------------------------

    @staticmethod
    def _token(authorization: str | None) -> str:
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise OidcRefused("no bearer token", 401)
        return token.strip()

    def _kid(self, token: str) -> str:
        jwt = _jwt()
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise OidcRefused("malformed token", 401) from exc
        kid = header.get("kid")
        if header.get("alg") != "RS256" or not isinstance(kid, str):
            raise OidcRefused("token is not an RS256 Google ID token")
        return kid

    def _check(self, token: str, key: Any) -> dict[str, Any]:
        jwt = _jwt()
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuers,
                # Time is checked below against the injectable clock.
                options={
                    "verify_exp": False,
                    "verify_iat": False,
                    "verify_nbf": False,
                    "require": ["exp", "iat", "aud", "iss", "email"],
                },
            )
        except jwt.PyJWTError as exc:
            raise OidcRefused(f"token rejected ({type(exc).__name__})") from exc
        now = self.clock().timestamp()
        if float(claims["exp"]) < now - self.skew.total_seconds():
            raise OidcRefused("token expired")
        if float(claims["iat"]) > now + self.skew.total_seconds():
            raise OidcRefused("token issued in the future")
        if claims.get("email_verified") is not True:
            raise OidcRefused("caller email not verified")
        email = str(claims["email"]).strip().lower()
        if not any(secrets.compare_digest(email, allowed) for allowed in self.callers):
            raise OidcRefused("token belongs to another account")
        return claims

    def verify(self, authorization: str | None) -> dict[str, Any]:
        """Verify synchronously; returns the token claims or raises ``OidcRefused``."""
        token = self._token(authorization)
        kid = self._kid(token)
        if self._needs_fetch(kid):
            self._fetch_keys()
        return self._check(token, self._cached_key(kid))

    async def averify(self, authorization: str | None) -> dict[str, Any]:
        """Verify without blocking the event loop; returns the claims or raises ``OidcRefused``."""
        token = self._token(authorization)
        kid = self._kid(token)
        if self._needs_fetch(kid):
            await self._afetch_keys()
        return self._check(token, self._cached_key(kid))


VerifierSource = GoogleOidcVerifier | Callable[[Request], GoogleOidcVerifier | None] | None


def require_google_oidc(source: VerifierSource) -> Callable[[Request], Any]:
    """FastAPI dependency: verify the caller, return the claims.

    ``source`` is a verifier, ``None`` (route disabled) or a callable receiving the request (for
    example ``lambda r: r.app.state.ops_verifier``). No verifier: 404. Refused: 401, 403 or 503
    with the generic detail "Not allowed"; the reason is logged as a warning.
    """

    async def dependency(request: Request) -> dict[str, Any]:
        verifier = source(request) if callable(source) and not isinstance(source, GoogleOidcVerifier) else source
        if verifier is None:
            raise HTTPException(status_code=404, detail="Not Found")
        try:
            return await verifier.averify(request.headers.get("authorization"))
        except OidcRefused as refused:
            logger.warning("OIDC caller refused on %s: %s", request.url.path, refused.reason)
            raise HTTPException(status_code=refused.status, detail="Not allowed") from None

    return dependency
