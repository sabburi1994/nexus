# Adopting Nexus in a platform app

A short guide for moving an existing FastAPI backend onto `create_nexus_app` and the shared backend
kit (`nexus.api`, `nexus.ai.spend`). Every piece is optional: adopt the factory first, then replace
local copies one at a time. For the React side see `packages/ui/README.md`
(`npm install @nexus-agent-framework/tokens @nexus-agent-framework/ui`).

## 1. Install

From PyPI, pinned to a version (0.5.0 has everything in this guide; coming from 0.4.0, read
[Upgrading from 0.4.0](#upgrading-from-040) first):

```text
# requirements.txt / pyproject dependency
nexus-agent-framework==0.5.0
# with the OIDC verifier (Cloud Scheduler or service account callers):
nexus-agent-framework[oidc]==0.5.0
```

To use a change that is merged on `main` but not released yet, pin the commit instead:
`nexus-agent-framework[oidc] @ git+https://github.com/sabburi1994/nexus.git@<commit>`.

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
        no_store_prefixes=("/api/",),  # API JSON (personal data) is never stored by browsers or proxies
    ),
)
```

Use `app = create_nexus_app(...)`. (The tuple form `app, db = ...` also works and gives an in memory
placeholder session; real apps keep their own database code.)

What the factory adds:

| Feature | Behaviour |
| :--- | :--- |
| Request id | `X-Request-ID` taken from the caller (a plain token up to 128 characters) or generated, echoed on every response with `X-Process-Time`; plain ASGI, so body size limits (413) and streaming pass through unchanged |
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
| 429 | `ai_disabled` | `MonthlyBudget` cap is 0 (AI switched off) | |
| 503 | `ai_budget_unavailable` | the spend ledger cannot be read (fail closed) | |

The body is flat: `message` sits at the top level next to `error`, not inside it.

```json
{"error": "ai_budget_exhausted", "message": "The monthly AI budget is used up. AI features resume next month.", "month": "2026-11", "request_id": "nex-3f2a9c81d0e4"}
```

A frontend that reads `body.error.message` (a nested shape some apps used before) gets `undefined`;
read `body.message`, and switch on `body.error` for the code.

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
from nexus.ai.spend import MonthlyBudget, SqlSpendLedger, parse_budget_cap, spend_table

ledger = SqlSpendLedger(engine)  # the app's Engine or AsyncEngine
# Migrations: add spend_table(Base.metadata) to your metadata, or call `await ledger.create_table()`.
# parse_budget_cap reads a setting: "", "none" or "unlimited" give None; "0" gives 0; negative raises.
budget = MonthlyBudget(ledger, cap_usd=parse_budget_cap(settings.monthly_ai_budget_usd))


async def ask_model(prompt: str) -> str:
    await budget.ensure_within_budget()  # raises MonthlyBudgetExceeded (rendered as 429)
    response = gemini.generate(prompt)
    await budget.record(response.cost_usd, response.model, task="brief", subject=user_id)
    return response.text


def ask_model_in_a_worker_thread(prompt: str) -> str:  # sync code: same budget, sync methods
    budget.ensure_within_budget_sync()
    response = gemini.generate(prompt)
    budget.record_sync(response.cost_usd, response.model, task="brief")
    return response.text


@app.get("/api/ai/budget")
async def ai_budget() -> dict:
    return await budget.summary()
```

* `cap_usd`: **`None` means no cap** (spend is only recorded); **`0` switches AI off**, so every
  billed call is refused with `ai_disabled` (429) without touching the ledger; a positive number is
  the monthly cap; **a negative number is a configuration error** (`ValueError` when the budget is
  built, so the app fails at startup instead of running without a cap).
* Months are UTC calendar months. The over-budget decision is cached for 20 seconds; `record`
  clears the cache.
* Sync code (model calls in worker threads, `run_in_threadpool`) uses `ensure_within_budget_sync`,
  `record_sync` and `summary_sync`. They need a ledger with a sync side: `InMemorySpendLedger`, or
  `SqlSpendLedger` over a sync `Engine` (over an `AsyncEngine` they raise `NotImplementedError`).
* **Fails closed by default:** if the ledger cannot be read, billed calls are refused with
  `ai_budget_unavailable` (503). klassesall's current gate fails open; pass `fail_closed=False` only
  if that is the owner's decision.
* `record` is best effort (logs and carries on); `strict=True` raises instead.
* An app with an existing ledger table can keep it: subclass `SpendLedger` (two async methods,
  `record` and `month_total`, plus `record_sync` and `month_total_sync` if sync code uses it) over
  that table and pass it to `MonthlyBudget`.

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

1. Pin `nexus-agent-framework==0.5.0` (or a commit); replace `FastAPI(...)` with
   `create_nexus_app(...)` keeping health path, CSP and docs setting; run the app's tests.
2. Check the error bodies the frontend reads: `message` is top level, and 500 bodies no longer
   carry exception text.
3. Replace the local limiter, SPA mount, spend cap and OIDC verifier one at a time, each with the
   app's existing tests plus one test of the 429 / 503 bodies.
4. Delete the local copies once their tests pass on the shared version.

## Upgrading from 0.4.0

* **A cap of `0` now switches AI off.** In 0.4.0, `MonthlyBudget(cap_usd=0)` (and any cap of 0 or
  less) meant unlimited. From 0.5.0, `0` refuses every billed call (`ai_disabled`, 429), `None`
  means no cap, and a negative cap raises `ValueError` at startup. If you passed `0` to mean "no
  cap", pass `None` instead (or read the setting with `parse_budget_cap`, which maps an empty value,
  `none` or `unlimited` to `None`).
* **Error `message` is top level.** Nothing changed in the body (`{"error": code, "message": ...,
  "request_id": ...}`), but a frontend that reads `error.message` must read `message`. The new
  `ai_disabled` code joins the list in section 3.
* **Sync budget.** `ensure_within_budget_sync`, `record_sync` and `summary_sync` work from worker
  threads; use a sync `Engine` for `SqlSpendLedger` there.
* The request id middleware is plain ASGI now, so an app's own 413 body size limit is no longer
  turned into a 400 or 500. Caller supplied request ids that are not a plain token are replaced.
* `SecurityHeadersConfig(no_store_prefixes=("/api/",))` sends `Cache-Control: no-store` on API
  responses (any status) unless the route set its own `Cache-Control`.
