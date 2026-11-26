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

Found by the run and not yet fixed (follow ups):

1. The full stack prompt's field name `backend_models_py` leaks into imports.
2. The normalizer does not rewrite wrong import paths for Nexus symbols (`nexus.models` to `nexus.db`).
3. The tuple form of `create_nexus_app` hands generated code a fake database.
4. `nexus.ai.client` caches an access token for a flat 40 minutes from when it fetched it, not until
   it expires, and never retries a 401: the first run lost its last three ideas to 401s after 39
   minutes. The benchmark now refreshes the token and retries once (a workaround in the benchmark,
   not a fix in the client); the rerun of those ideas needed no refresh.
5. `nexus.ai.pricing` prices gemini-3.8-flash at 0.075 and 0.30 USD per million tokens, roughly ten
   times below the 0.75 and 3.75 the platform apps use, so the squad's 1.00 USD budget undercounts.
   The eight ideas' tokens cost 0.13 USD at the framework's prices, 1.61 USD at the platform apps'
   prices and 2.15 USD at the benchmark's.

Total spend for this measurement: about 2.58 USD at the benchmark's prices (a one idea smoke run,
the eight ideas, and three ideas rerun after the 401s), billed to the showcase's host project.
