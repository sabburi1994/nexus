# Adopting Nexus in a platform app

A short guide for moving an existing FastAPI backend onto `create_nexus_app` and the shared backend
kit (`nexus.api`, `nexus.ai.spend`). Every piece is optional: adopt the factory first, then replace
local copies one at a time. For the React side see `packages/ui/README.md`.

## 1. Install (pinned to a commit)

PyPI still serves 0.1.1, so pin the git commit you were given:

```text
# requirements.txt / pyproject dependency
nexus-agent-framework @ git+https://github.com/sabburi1994/nexus.git@<commit>
# with the OIDC verifier (Cloud Scheduler or service account callers):
nexus-agent-framework[oidc] @ git+https://github.com/sabburi1994/nexus.git@<commit>
```

The factory alone needs only FastAPI, Starlette, httpx, Pydantic and SQLAlchemy (already in every
app). `[oidc]` adds PyJWT with crypto. Nothing else is pulled in.

## 2. Create the app

```python
from nexus.api import SecurityHeadersConfig, create_nexus_app

APP_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; "
    "form-action 'self'; frame-ancestors 'none'"
)

app = create_nexus_app(
    title="FinHub API",
    version=APP_VERSION,
    docs=False,  # private app: no /docs, no /openapi.json
    health_path="/health",  # keep the path your probes and uptime checks already use
    ready_path=None,  # or "/ready"; None drops the readiness route
    cors_origins=None,  # same origin only (default); list explicit origins otherwise
    security_headers=SecurityHeadersConfig(
        content_security_policy=APP_CSP,  # your existing policy, unchanged
        immutable_prefixes=("/assets/",),  # hashed Vite assets cached for a year
    ),
)
```

Use `app = create_nexus_app(...)`. (The tuple form `app, db = ...` also works and gives an in memory
placeholder session; real apps keep their own database code.)

What the factory adds:

| Feature | Behaviour |
| :--- | :--- |
| Request id | `X-Request-ID` taken from the caller or generated, echoed on every response with `X-Process-Time` |
| Health | `GET` and `HEAD` on `health_path` (and `ready_path`), JSON with app and framework version |
| CORS | closed unless `cors_origins` is set; credentials only with explicit origins |
| Security headers | opt in; CSP per path, HSTS, nosniff, frame DENY, same-origin referrer, permissions policy, cache rules |
| Errors | the error contract below |

Keeping existing behaviour:

* Register your own routers, middleware and exception handlers after the factory, as before. A
  handler you register for `Exception` replaces the Nexus one (the command center does this).
* Middleware added later runs first. Keep any app specific middleware that must see every request
  (for example a WAF) added after the factory.
* If the app already sends security headers, either drop its middleware and pass the same policy in
  `SecurityHeadersConfig`, or leave `security_headers` off. Headers already set are never overwritten.

## 3. Error contract

Every error the kit produces is JSON with `error` (a stable code), `message` (safe to show) and
`request_id` (also in the `X-Request-ID` header). Exception text is never sent to clients; the full
exception is logged server side on `nexus.api` with the same request id.

| Status | `error` | When | Extra fields |
| :--- | :--- | :--- | :--- |
| 500 | `internal_server_error` | any unhandled exception | |
| 429 | `rate_limited` | a rate limit was hit | `retry_after` (also `Retry-After` header) |
| 429 | `ai_budget_exhausted` | `MonthlyBudget` cap reached | `month` |
| 503 | `ai_budget_unavailable` | the spend ledger cannot be read (fail closed) | |

`HTTPException`s you raise keep FastAPI's shape (`{"detail": ...}`) and status. The OIDC dependency
answers 401, 403 or 503 with `{"detail": "Not allowed"}` and 404 when not configured.

## 4. Rate limiting (`nexus.api.ratelimit`)

Replaces app local limiters (klassesall `core/ratelimit.py`, the showcase limiter).

```python
from fastapi import Depends
from nexus.api import (RateLimitMiddleware, RateLimitRule, SlidingWindowLimiter, ip_and_credential_key,
                       ip_key, rate_limit)

HOPS = 1 if os.getenv("K_SERVICE") else 0   # Cloud Run appends the real client address last

# Per route
scan_limit = SlidingWindowLimiter(limit=5, window_seconds=60)
@app.post("/api/scan", dependencies=[Depends(rate_limit(scan_limit, ip_key(HOPS)))])
async def scan(...): ...

# App wide by path (first matching rule wins; health paths and OPTIONS are never limited)
app.add_middleware(
    RateLimitMiddleware,
    key=ip_and_credential_key(HOPS),        # signed in users behind one address get their own budget
    rules=[
        RateLimitRule(SlidingWindowLimiter(10, 60), ("/api/auth/",), frozenset({"POST"})),
        RateLimitRule(SlidingWindowLimiter(120, 60), ("/api/",)),
    ],
    enabled=settings.app_env != "test",
)
```

Counters live in memory per instance: with `max_instance_count = 2` the effective limit is up to
twice the configured one. Credentials in keys are hashed, never stored as is.

## 5. Serving the frontend (`nexus.api.spa`)

Replaces `register_frontend` (PredictiveEconomics) and `serve_spa` / `spa_file` (FinHub).

```python
from nexus.api import mount_spa

app.include_router(api_router)  # every API route first
mount_spa(app, Path(__file__).parent / "static")  # the Vite dist; register last
```

* Files are resolved inside the folder only (encoded `..`, absolute paths, NUL, outward symlinks
  refused).
* `assets/*` is `immutable` for a year; `index.html`, `sw.js`, `registerSW.js`,
  `manifest.webmanifest`, `theme-init.js` are `no-cache` (pass `no_cache_files=` to change the list).
* Unknown paths fall back to `index.html`; paths under `api`, `internal`, `health`, `docs` ... answer
  a JSON 404 instead (`api_prefixes=`). A missing hashed asset is a 404, never `index.html`.
* Content types are explicit (`.js` is `text/javascript` even on Windows).

## 6. Monthly AI spend (`nexus.ai.spend`)

Replaces app local spend caps (klassesall `services/llm/budget.py`, FinHub `spending.py`,
PredictiveEconomics' budgeted analyst).

```python
from nexus.ai.spend import MonthlyBudget, SqlSpendLedger, spend_table

ledger = SqlSpendLedger(engine)  # the app's Engine or AsyncEngine
# Migrations: add spend_table(Base.metadata) to your metadata, or call `await ledger.create_table()`.
budget = MonthlyBudget(ledger, cap_usd=settings.monthly_ai_budget_usd)  # 0 or less: unlimited


async def ask_model(prompt: str) -> str:
    await budget.ensure_within_budget()  # raises MonthlyBudgetExceeded (rendered as 429)
    response = gemini.generate(prompt)
    await budget.record(response.cost_usd, response.model, task="brief", subject=user_id)
    return response.text


@app.get("/api/ai/budget")
async def ai_budget() -> dict:
    return await budget.summary()
```

* Months are UTC calendar months. The over-budget decision is cached for 20 seconds; `record`
  clears the cache.
* **Fails closed by default:** if the ledger cannot be read, billed calls are refused with
  `ai_budget_unavailable` (503). klassesall's current gate fails open; pass `fail_closed=False` only
  if that is the owner's decision.
* `record` is best effort (logs and carries on); `strict=True` raises instead.
* An app with an existing ledger table can keep it: subclass `SpendLedger` (two async methods,
  `record` and `month_total`) over that table and pass it to `MonthlyBudget`.

## 7. Cloud Scheduler and service account callers (`nexus.api.oidc`)

Replaces `TickVerifier` (FinHub) and the `OidcVerifier` copies in the ops routes.

```python
from typing import Any
from fastapi import Depends
from nexus.api import GoogleOidcVerifier, require_google_oidc

# At startup: None when not configured (laptop, tests), and the route then answers 404.
app.state.ops_verifier = GoogleOidcVerifier.from_settings(
    settings.ops_audience,  # the URL Cloud Scheduler targets (its OIDC audience)
    settings.ops_callers,  # service account email(s), comma separated allowed
)


@app.post("/internal/scheduler/tick", include_in_schema=False)
async def tick(claims: dict[str, Any] = Depends(require_google_oidc(lambda r: r.app.state.ops_verifier))): ...
```

Checks: RS256 signature against Google's published keys (cached one hour, refreshed when a new key
id appears), audience, Google issuer, expiry and issue time with two minutes of skew,
`email_verified`, exact caller email. Status: 401 no usable token, 403 wrong caller or token, 503
Google's keys unavailable; the reason is logged as a warning, never returned. Sync code can call
`verifier.verify(authorization)` (raises `OidcRefused` with `.status`).

## 8. Checklist per app

1. Pin the commit; replace `FastAPI(...)` with `create_nexus_app(...)` keeping health path, CSP and
   docs setting; run the app's tests.
2. Check the error bodies the frontend reads: 500 bodies no longer carry exception text.
3. Replace the local limiter, SPA mount, spend cap and OIDC verifier one at a time, each with the
   app's existing tests plus one test of the 429 / 503 bodies.
4. Delete the local copies once their tests pass on the shared version.
