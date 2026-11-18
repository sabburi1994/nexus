# Nexus benchmarks

Measured numbers for accuracy and performance changes. Every accuracy or performance PR quotes a
before and after run of the relevant script. By default nothing here calls a paid model: the
providers are the showcase's deterministic squad and `MockProvider`. The `vertex` provider of
`bench_generation.py` calls a real Gemini model and is paid (see "Real model runs").

Both scripts execute generated code (pytest, uvicorn) in subprocesses on this machine. Run them from
an environment where this checkout is installed (`pip install -e ".[dev]"`), so the generated apps
import this version of `nexus`.

| Script | Question it answers |
| :--- | :--- |
| `bench_generation.py` | For a fixed set of 8 ideas: does each generated app compile, start (`/health` 200 under uvicorn) and pass its own tests end to end? Time per stage, prompt and output size per stage, test run time, healing cycles. |
| `bench_output_defects.py` | Does the pipeline absorb realistic model output defects (markdown fences, prose, double escaping, BOM, CRLF, wrong import roots, missing imports)? One defect injected into otherwise passing output, self healing off. |

```bash
python benchmarks/bench_generation.py                 # deterministic and mock, 8 ideas
python benchmarks/bench_output_defects.py --ideas 3   # 12 defect types plus a clean control
# Paid: a real Gemini model on Vertex AI, with hard spend caps (needs gcloud auth login)
python benchmarks/bench_generation.py --providers vertex --project <gcp project> --max-spend-usd 5
```

The `vertex` provider counts spend itself from every response's `usageMetadata` (input, output and
thinking tokens, including calls whose output then fails to parse) at `--price-in` and `--price-out`
(default 1 and 5 USD per million, deliberately above list price), and refuses the next call once
`--max-spend-usd` (run) or `--per-idea-spend-usd` (idea) is reached. `--from-idea N` resumes a
stopped run.

The idea list in `bench_generation.py` is fixed; append new ideas at the end so earlier numbers stay
comparable.

## Results log

| Date | Commit | Benchmark | Result |
| :--- | :--- | :--- | :--- |
| 2026-11-15 | ea8afc2 (0.3.3) | defects | 4/12 defect types absorbed, 12/36 cases pass |
| 2026-11-15 | ea8afc2 (0.3.3) | generation, deterministic | 8/8 end to end; median 4.6 s per run, of which 4.5 s are 2 pytest runs |
| 2026-11-15 | ea8afc2 (0.3.3) | generation, mock | 0/8 end to end (placeholder output) |
| 2026-11-15 | 0.3.4 (code normalizer) | defects | 12/12 defect types absorbed, 36/36 cases pass |
| 2026-11-15 | 0.3.4 (code normalizer) | generation, deterministic | 8/8 end to end; median 4.6 s (unchanged) |
| 2026-11-17 | 0.5.1 | generation, **real model** (gemini-3.8-flash, Vertex AI) | **6/8 end to end**; 8/8 build, 6/8 start, 6/8 tests pass; 2/8 without healing; median 386 s and about 0.29 USD per idea |
| 2026-11-18 | 0.5.2 | generation, **real model** (gemini-3.8-flash, Vertex AI) | **8/8 end to end**; 6/8 without healing; median 8 endpoint tests per app; median 253 s and about 0.20 USD per idea |

## Real model runs

### 2026-11-17, 0.5.1, gemini-3.8-flash on Vertex AI (global endpoint)

First measurement of the squad against a real model. Settings: default squad (`max_healing_cycles`
3, squad budget 1.00 USD), temperature as shipped (structured calls 0.0, thinking level low), one
run per idea. Spend at the benchmark's prices (1 and 5 USD per million tokens).

| # | Idea | Builds | Starts | Tests | Healing cycles | Time | Spend |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Treasury ledger triage | yes | yes | pass | 0 | 204 s | 0.16 |
| 2 | Luxury watch price alerts | yes | yes | pass | 0 | 376 s | 0.14 |
| 3 | Food bank volunteer scheduler | yes | yes | pass | 2 | 397 s | 0.20 |
| 4 | Clinic appointment reminders | yes | yes | pass | 3 | 730 s | 0.34 |
| 5 | Bike sharing availability dashboard | yes | **no** | **fail** (1 of 3) | 3 | 507 s | 0.36 |
| 6 | Recipe cost calculator | yes | **no** | **error** (collection) | 3 | 405 s | 0.36 |
| 7 | IT asset inventory, warranty alerts | yes | yes | pass | 3 | 366 s | 0.32 |
| 8 | Language exchange partner matching | yes | yes | pass | 2 | 289 s | 0.26 |

**6/8 end to end** (compiles, `/health` 200 under uvicorn, own pytest suite passes). Only 2/8 pass on
the first try: self healing turned 4 failing apps into passing ones, so the loop does real work.
Tokens for the 8 ideas: about 116 000 input and 407 000 output (no thinking tokens reported).
Almost all time is model latency (generation is 96 % of the run); the generated test runs take
about 5 s each. The generated suites are small (3 or 4 tests per app), so "tests pass" is a low
bar: it shows the app imports, starts and serves its main routes, not that its logic is right.

Both failures trace back to the framework, not to model randomness:

* **Recipe cost calculator**: `backend_models.py` imports `NexusEntity` from `nexus.models`, which
  does not exist (it is `nexus.db`). The code normalizer adds missing imports but does not rewrite a
  wrong one. The same error sank the first smoke run (treasury idea) together with an import of
  `backend_models_py`, the prompt's field name, instead of the module `backend_models`.
* **Bike sharing**: the model used the tuple form `app, db = create_nexus_app(...)`, whose `db` is an
  in memory placeholder, and then treated it as a SQLAlchemy session.

Found by the run (all fixed in 0.5.2, see the next section):

1. The full stack prompt's field name `backend_models_py` leaks into imports.
2. The normalizer does not rewrite wrong import paths for Nexus symbols (`nexus.models` to `nexus.db`).
3. The tuple form of `create_nexus_app` hands generated code a fake database.
4. `nexus.ai.client` caches an access token for a flat 40 minutes from when it fetched it, not until
   it expires, and never retries a 401: the first run lost its last three ideas to 401s after 39
   minutes. That rerun used a token refresh in the benchmark as a workaround; 0.5.2 fixes the
   client and the workaround is gone.
5. `nexus.ai.pricing` prices gemini-3.8-flash at 0.075 and 0.30 USD per million tokens, ten times
   below the Vertex AI list price of 0.75 and 3.75 (0.075 is the cached input price), so the squad's
   1.00 USD budget undercounts.
   The eight ideas' tokens cost 0.13 USD at the framework's prices, 1.61 USD at the platform apps'
   prices and 2.15 USD at the benchmark's.

Total spend for this measurement: about 2.58 USD at the benchmark's prices (a one idea smoke run,
the eight ideas, and three ideas rerun after the 401s), billed to the showcase's host project.

### 2026-11-18, 0.5.2 (fixes from the run above), gemini-3.8-flash on Vertex AI

Same settings and idea list. 0.5.2 fixes the five defects above and four more that the reruns
uncovered (see `CHANGELOG.md`). Final run:

| # | Idea | Builds | Starts | Tests (all passing) | Healing cycles | Time | Spend |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Treasury ledger triage | yes | yes | 5 | 0 | 218 s | 0.18 |
| 2 | Luxury watch price alerts | yes | yes | 8 | 0 | 215 s | 0.19 |
| 3 | Food bank volunteer scheduler | yes | yes | 11 | 0 | 221 s | 0.19 |
| 4 | Clinic appointment reminders | yes | yes | 5 | 1 | 354 s | 0.26 |
| 5 | Bike sharing availability dashboard | yes | yes | 8 | 0 | 427 s | 0.19 |
| 6 | Recipe cost calculator | yes | yes | 6 | 0 | 284 s | 0.23 |
| 7 | IT asset inventory, warranty alerts | yes | yes | 8 | 1 | 485 s | 0.36 |
| 8 | Language exchange partner matching | yes | yes | 8 | 0 | 215 s | 0.20 |

**8/8 end to end, 6/8 without healing.** The suites now run the app's startup (seeding a fresh
SQLite database) and call 5 to 18 distinct endpoints per app, against 3 or 4 tests per app in the
0.5.1 run. Tokens: about 128 000 input and 335 000 output, 1.35 USD at list price for the eight.

How it got there (each row is a full run of the eight ideas; numbers are honest, including the
regressions):

| Run | Change | End to end | Without healing | Tests per app | What it showed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| A | 0.5.1 as published | 6/8 | 2/8 | 3 to 4 | the five defects above |
| B | prompt layout, import rewrites, token, pricing fixes | 2/8 | 6/8 | 2 to 3 | apps now use a real database; integer foreign keys to `NexusEntity`'s UUID ids crash the first start (tests skipped startup, so QA never saw it) |
| C | `NexusEntity` on generic `Uuid`, UUID rule in the prompt, tests run startup | 6/8 | 5/8 | 1 to 3 | a test asserting the exact `/health` title; a database kept between healing cycles with the old schema |
| D | fresh database per test run, `/health` rule | 8/8 (6 ran, 2 lost to a network outage, rerun) | 8/8 | 1 to 4 | **tests only called `/health`**: QA saw the first 3500 characters of main.py, which now end before the routes |
| E | QA sees all of main.py and the models, gets the route list, must test each route; transport retries | **8/8** | **6/8** | **5 to 11** | final |

Limits of this measurement:

* One run per idea; a repeat can differ by an idea or two. Run each idea several times before
  quoting a rate.
* The tests are written by the same model that wrote the code. A pass means the app starts and its
  endpoints do what the generated tests expect, not that the business logic is right.
* Only the backend is checked. The generated React frontend, Dockerfile and Terraform are not
  built or deployed by this benchmark.
* Generated apps are small: two Python modules on SQLite, no authentication, no migrations.

Total spend for the 0.5.1 and 0.5.2 measurements together: about 7.04 USD at list price (9.39 at
the benchmark's deliberately high prices), billed to the showcase's host project.
