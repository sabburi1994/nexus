# Changelog

All notable changes to the Nexus packages. Versions follow [Semantic Versioning](https://semver.org/);
dates are UTC. Release pages: [GitHub releases](https://github.com/sabburi1994/nexus/releases).

## Latest stable versions

| Package | Registry | Latest stable | Released |
| :--- | :--- | :--- | :--- |
| [`nexus-agent-framework`](https://pypi.org/project/nexus-agent-framework/) | PyPI | **0.5.1** | 2026-11-17 |
| [`@nexus-agent-framework/tokens`](https://www.npmjs.com/package/@nexus-agent-framework/tokens) | npm | **1.0.1** | 2026-11-17 |
| [`@nexus-agent-framework/ui`](https://www.npmjs.com/package/@nexus-agent-framework/ui) | npm | **1.0.2** | 2026-11-17 |
| [`@nexus-agent-framework/contracts`](https://www.npmjs.com/package/@nexus-agent-framework/contracts) | npm | **1.0.4** | 2026-11-17 |
| [`@nexus-agent-framework/middleware`](https://www.npmjs.com/package/@nexus-agent-framework/middleware) | npm | **1.0.3** | 2026-11-17 |
| [`@nexus-agent-framework/scraper`](https://www.npmjs.com/package/@nexus-agent-framework/scraper) | npm | **1.0.3** | 2026-11-17 |

Install: `pip install nexus-agent-framework` and
`npm install @nexus-agent-framework/tokens @nexus-agent-framework/ui`.

---

## Python: `nexus-agent-framework`

### 0.5.2 (unreleased)

Fixes found by the first real model benchmark (`benchmarks/README.md`, "Real model runs").

* **Pricing:** `nexus.ai.pricing` used 0.075 and 0.30 USD per million tokens for gemini-3.8-flash
  (the cached input price), about ten times below the list price, so the squad's spend cap
  undercounted. Prices now follow the Vertex AI list (global endpoint): 0.75 and 3.75 until
  2026-12-31, 1.50 and 7.50 from 2027-01-01, chosen by date (`price_per_million(model, on=...)`).
  Unknown models are priced at the highest known Flash price, so a cap never undercounts them.
  Thinking tokens now count as output in `generate` and `converse` too (they already did in
  `structured`).
* **Access tokens:** a token from the metadata server is reused until 5 minutes before it expires,
  a gcloud token for 5 minutes (gcloud may hand out a token minted up to an hour earlier), and a
  401 drops the cached token and retries once with a fresh one. Before, a token was reused for 40
  minutes from when Nexus fetched it and long runs failed with 401. New `invalidate_gcp_access_token()`.
* **Generated apps:** the full stack prompt states the file layout and the exact imports
  (`from backend_models import ...`, `from nexus.db import Base, NexusEntity`), asks for
  `app = create_nexus_app(...)` with a real SQLAlchemy session instead of the in memory placeholder
  of the tuple form, and keeps model and network calls out of import time. The heal prompt now shows
  both backend files (the models file was never shown, so errors in it could not be healed).
* **Code normalizer:** imports of the prompt's field names (`backend_models_py`, `backend_main_py`)
  become the real modules, and known Nexus names imported from a module that does not provide them
  (`from nexus.models import NexusEntity`) move to their real module.
* **`NexusEntity`** uses SQLAlchemy's generic `Uuid` (native UUID on PostgreSQL, CHAR(32) on SQLite)
  instead of the PostgreSQL only type, and the prompt states that its ids and every foreign key to
  it are UUIDs. Generated apps declared integer foreign keys and crashed on their first start.
* **QA:** generated tests use `with TestClient(app) as client`, so startup handlers run and a
  startup crash fails the QA gate; they assert only `status` and `healthy` of `/health`. Every
  generated test run gets a fresh SQLite database through `DATABASE_URL` (a database left by an
  earlier healing cycle kept the old schema and failed with "no such column").
* **Network:** `GeminiClient` retries every transport error (dropped connections, brief DNS
  failures, timeouts) up to 3 times with a growing pause, not only timeouts.
* **Measured** with the real model benchmark: see `benchmarks/README.md`.

### 0.5.1 (2026-11-17)

Documentation and package metadata only; no code changes from 0.5.0.

* The PyPI page shows the latest stable versions, the release notes and the backend adoption kit.
* `CHANGELOG.md` added; the PyPI project links point to it and to the GitHub releases.

### 0.5.0 (2026-11-16)

Adoption fixes reported by the first platform apps. **Read "Upgrading from 0.4.0" below.**

* **Breaking: a monthly AI budget cap of `0` now switches AI off.** `MonthlyBudget(cap_usd=0)`
  refuses every billed call with `AiSpendDisabled` (HTTP 429, error code `ai_disabled`) without
  reading the ledger. `None` means no cap. A negative or non numeric cap raises `ValueError` when
  the budget is built, so a bad setting fails at startup. In 0.4.0 a cap of 0 or less meant
  unlimited.
* `parse_budget_cap(value)` reads a cap from configuration: empty, `none` or `unlimited` give
  `None`, a number gives the cap in USD.
* **Sync budget API** for model calls made from worker threads: `ensure_within_budget_sync`,
  `record_sync`, `summary_sync`. `SpendLedger` gains `record_sync` and `month_total_sync`
  (implemented by `InMemorySpendLedger` and by `SqlSpendLedger` over a sync `Engine`).
* **Request id middleware is plain ASGI.** `NexusTelemetryMiddleware` no longer uses Starlette's
  `BaseHTTPMiddleware`, so an app's own 413 body size limit is no longer turned into a 400 or 500,
  and streaming bodies pass through untouched. A caller supplied `X-Request-ID` must be a plain
  token of at most 128 characters, otherwise a new id is generated.
* `SecurityHeadersConfig(no_store_prefixes=("/api/",))` sends `Cache-Control: no-store` on
  matching paths for every status, unless the route set its own `Cache-Control`.
* `docs/ADOPTING.md`: the error body is flat (`message` sits next to `error`), the `ai_disabled`
  code, the cap rules, the sync API and an upgrade section.

#### Upgrading from 0.4.0

* If you passed `cap_usd=0` to mean "no cap", pass `None` (or read the setting with
  `parse_budget_cap`). A cap of 0 now turns AI features off.
* Frontends read the error text from the top level `message` field, never `error.message`.
* Sync code can now use the `*_sync` budget methods instead of running the async ones in a loop.

### 0.4.0 (2026-11-16)

The backend adoption kit, so the platform apps stop keeping their own copies.

* `nexus.api.ratelimit`: `SlidingWindowLimiter` (bounded key count), `client_ip` with trusted proxy
  hops, the `rate_limit` route dependency and `RateLimitMiddleware` with path rules. Rejections use
  the error contract (429 `rate_limited` with `retry_after` and a `Retry-After` header).
* `nexus.api.spa`: `mount_spa` serves a Vite build safely (no path escapes, immutable hashed
  assets, `no-cache` HTML, JSON 404s for API prefixes, explicit content types).
* `nexus.ai.spend`: a persistent monthly AI spend ledger (`SqlSpendLedger` over the app's own
  engine, `InMemorySpendLedger`) and `MonthlyBudget`, which fails closed when the ledger cannot be
  read (503 `ai_budget_unavailable`) and refuses calls past the cap (429 `ai_budget_exhausted`).
* `nexus.api.oidc`: `GoogleOidcVerifier` and `require_google_oidc` for Cloud Scheduler and service
  account callers (extra `[oidc]`).
* `create_nexus_app` options: `docs=False`, `health_path`, `ready_path`; `HEAD` on health routes.
* `docs/ADOPTING.md`, a step by step guide for moving an existing FastAPI app onto the kit.

### 0.3.x (2026-11-14 and 2026-11-15, tagged, not published to PyPI)

* 0.3.5: unhandled exceptions return a generic 500 body (`internal_server_error` with the request
  id); the exception text is logged server side, never sent to the client.
* 0.3.4: model returned code is normalized before it is written (markdown fences, prose, double
  escaping, BOM and CRLF, import layout); generation and accuracy benchmarks added.
* 0.3.3: the `nexus new` scaffold builds, starts and passes its own tests (non root container,
  checked app names, a starter test suite).
* 0.3.2: `nexus dream` runs the generated test suite for real (Stage 1 healing works on real
  pytest output), a spend cap for the whole squad run, fixed platform templates for Terraform,
  the Dockerfile and the deploy script of generated apps.
* 0.3.1: `NexusSecurityHeadersMiddleware` and `SecurityHeadersConfig` (CSP per path, HSTS,
  nosniff, frame DENY, referrer and permissions policy, cache rules for static assets).
* 0.3.0: closed CORS by default, API hardening, platform Terraform modules (`nexus_app`,
  `nexus_cloud_run`), the showcase on its own Terraform configuration.

### 0.1.0 and 0.1.1 (2026-11-10)

First releases on PyPI: the orchestrator, the seven agent IT squad (`nexus dream`), the MCP server
(`nexus mcp`), the local dashboard (`nexus ui`), Stage 1 to 3 (self healing, brownfield audit and
blast radius, ROI estimates).

---

## npm: `@nexus-agent-framework/tokens`

### 1.0.1 (2026-11-17)

Documentation only: the npm page lists the latest stable versions and links to this changelog.
The package contents other than the README and `package.json` are the same as 1.0.0.

### 1.0.0 (2026-11-16)

First release: CSS custom properties for colour roles, type, spacing, radius, shadows, focus ring,
motion and layout; a light and a dark theme per platform app; Tailwind 3 and 4 presets; typed
values and WCAG AA contrast helpers (every theme is tested).

## npm: `@nexus-agent-framework/ui`

### 1.0.2 (2026-11-17)

Documentation only: the npm page lists the latest stable versions and links to this changelog.
No component changes from 1.0.1.

### 1.0.1 (2026-11-16)

* `LineChart` no longer widens the page on phones: its screen reader data table is clipped inside a
  visually hidden wrapper, and `.nx-chart` is `position: relative`.

### 1.0.0 (2026-11-15, tag `ui-v1.0.0` only, not published to npm)

* The shared React kit for the platform apps: Button, form fields, Card, Table, Sheet, Dialog,
  Tabs, AppShell, Toast, SkeletonRows, EmptyState, ErrorState, Badge, Stat, LineChart. Plain CSS
  that works under a strict Content Security Policy, themed by the tokens package.
* The showcase components moved to the `@nexus-agent-framework/ui/showcase` entry point.

### 0.2.0 and earlier (2026-11-10 and 2026-11-11)

The showcase components (`NexusHeader`, `StatCard`, `CommandBlock` and others).

## npm: `@nexus-agent-framework/contracts`

### 1.0.4 (2026-11-17)

Documentation only: the npm page lists the latest stable versions and links to this changelog.
`dist` is byte for byte the same as 1.0.3.

### 1.0.3 (2026-11-11)

Telemetry schemas, Stage 1 to 3 healing, AST and ROI contracts, agent audit chains.

## npm: `@nexus-agent-framework/middleware`

### 1.0.3 (2026-11-17)

Documentation only: the npm page lists the latest stable versions and links to this changelog.
`dist` is byte for byte the same as 1.0.2.

### 1.0.2 (2026-11-11)

Security headers, a best effort credential sanitizer and correlation ids for Node servers
(Express, Fastify, Next.js, Hono).

## npm: `@nexus-agent-framework/scraper`

### 1.0.3 (2026-11-17)

Documentation only: the npm page lists the latest stable versions and links to this changelog.
`dist` is byte for byte the same as 1.0.2.

### 1.0.2 (2026-11-11)

Polite scraping policies (rate limits, payload caps, `robots.txt`, timeouts and backoff) and the
`ScrapedItem` data contract.
