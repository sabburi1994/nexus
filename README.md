# Nexus: Orchestrator-Native AI Agentic Framework

<p align="center">
  <a href="https://nexus.abburi.info"><img src="https://img.shields.io/badge/website-nexus.abburi.info-bd513d" alt="Website" /></a>
  <a href="https://nexus.abburi.info/#simulator"><img src="https://img.shields.io/badge/live%20simulator-interactive-172a2e" alt="Live Simulator" /></a>
  <a href="https://pypi.org/project/nexus-agent-framework/"><img src="https://img.shields.io/pypi/v/nexus-agent-framework?color=0284c7&label=PyPI%20package" alt="PyPI version" /></a>
  <a href="https://www.npmjs.com/org/nexus-agent-framework"><img src="https://img.shields.io/badge/npm-%40nexus--agent--framework-cb3837?logo=npm" alt="npm org" /></a>
  <a href="https://pypi.org/project/nexus-agent-framework/"><img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-3776ab?logo=python" alt="Python Versions" /></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/license-Apache%202.0-10b981.svg" alt="License" /></a>
  <a href="https://github.com/sabburi1994/nexus/actions"><img src="https://img.shields.io/badge/tests-30%2F30%20passed-emerald" alt="Tests" /></a>
</p>

> **Nexus** is an autonomous AI agentic software engineering framework that transforms requirements into production-ready full-stack applications. It provisions a full virtual IT department (BA, Solution Architect, Data Architect, UI Designer, Full-Stack Engineer, DevOps, and QA) and connects natively with **Claude Code, Cursor, Codex, and Gemini** via the Model Context Protocol (MCP).
>
> - **Platform Website & Docs**: [nexus.abburi.info](https://nexus.abburi.info)
> - **Live Stage 1–3 Simulator**: [nexus.abburi.info/#simulator](https://nexus.abburi.info/#simulator)
> - **Brownfield AST Explorer**: [nexus.abburi.info/#brownfield](https://nexus.abburi.info/#brownfield)

---

## 🚀 Installation & Quickstart

### Python Framework (PyPI)
Install the core orchestrator and agent runtime:
```bash
pip install nexus-agent-framework
```

### TypeScript / React Packages (npm)
Install individual enterprise contracts, UI components, and security middleware:
```bash
npm install @nexus-agent-framework/contracts
npm install @nexus-agent-framework/middleware
npm install @nexus-agent-framework/scraper
npm install @nexus-agent-framework/ui
```

---

## 🏛️ The Nexus Virtual IT Squad

Nexus simulates a real-world software engineering organization with 7 autonomous specialists working sequentially to deliver end-to-end applications:

```mermaid
flowchart TD
    User["Creator with an Idea<br/>(Vague Requirements)"] --> BA["1. Business Analyst<br/>(User Stories & Interactive HTML Mockup)"]
    BA --> SA["2. Solution Architect<br/>(System Topology & Cloud Choice)"]
    SA --> DA["3. Data Architect<br/>(ERD & SQL DDL Schema)"]
    DA --> Design["4. UI/UX Designer<br/>(Design Tokens & Component Specs)"]
    Design & DA --> FS["5. Full-Stack Engineer<br/>(React UI + FastAPI Backend)"]
    SA & DA --> DevOps["6. DevOps Engineer<br/>(Terraform IaC for target cloud)"]
    FS & DevOps --> QA["7. QA & Security Engineer<br/>(Preflight Guardrails & Test Suite)"]
    QA --> Repo["Delivered Application Workspace<br/>(Runnable Full-Stack Project on Disk)"]
```

### Specialist Responsibilities
1. **Business Analyst (`BusinessAnalystAgent`)**: Synthesizes ideas into a canonical slug, value proposition, user stories, and an interactive HTML wireframe preview (`docs/preview_mockup.html`).
2. **Solution Architect (`SolutionArchitectAgent`)**: Evaluates cloud runtime topology (Cloud Run serverless containers vs Always-Free VM), networking, and latency budgets.
3. **Data Architect (`DataArchitectAgent`)**: Normalizes relational schemas, foreign keys, indexes, and emits PostgreSQL SQL DDL (`docs/DATA_ARCHITECTURE.md`).
4. **UI/UX Designer (`UiDesignerAgent`)**: Produces responsive design tokens and Tailwind component structures utilizing `@nexus-agent-framework/ui`.
5. **Full-Stack Engineer (`FullStackEngineerAgent`)**: Implements clean FastAPI REST endpoints, Pydantic validation schemas, SQLAlchemy ORM entities, and React UI components.
6. **DevOps Engineer (`DevopsEngineerAgent`)**: Generates production Infrastructure as Code (Terraform `main.tf`, `variables.tf`), container definitions (`Dockerfile`, `docker-compose.yml`), and CI/CD pipelines.
7. **QA & Security Engineer (`QaEngineerAgent`)**: Executes pre-flight security scans (injection sanitization, CORS, credential checks) and delivers an executable `pytest` suite with 100% pre-flight clearance.

---

## 📦 Ecosystem Packages

Nexus is maintained as a unified monorepo providing full-stack libraries across PyPI and npm:

| Package | Registry | Version | Capabilities |
| :--- | :--- | :--- | :--- |
| **[`nexus-agent-framework`](https://pypi.org/project/nexus-agent-framework/)** | PyPI | `0.2.0` | Core orchestrator, 7 specialist agents, Stage 1–3 self-healing/brownfield/ROI, CLI (`dream`, `mcp`, `ui`, `audit`, `refactor`, `metrics`) |
| **[`@nexus-agent-framework/contracts`](https://www.npmjs.com/package/@nexus-agent-framework/contracts)** | npm | `1.0.3` | Telemetry schemas, Stage 1–3 healing/AST/ROI contracts, agent audit chains |
| **[`@nexus-agent-framework/middleware`](https://www.npmjs.com/package/@nexus-agent-framework/middleware)** | npm | `1.0.2` | Hardened security headers, zero-leak credential sanitizer, correlation tracing |
| **[`@nexus-agent-framework/scraper`](https://www.npmjs.com/package/@nexus-agent-framework/scraper)** | npm | `1.0.2` | Polite web scraping protocols, RSS feed ingestion, rate limits & backoff policies |
| **[`@nexus-agent-framework/ui`](https://www.npmjs.com/package/@nexus-agent-framework/ui)** | npm | `0.2.0` | Institutional paper React design system (`NexusHeader`, `StatCard`, `TraceViewer`, `HealingLoopPanel`, `BlastRadiusCard`, `RoiScorecard`, `CommandBlock`) |

---

## 🔌 Orchestrator-Native: Claude Code, Cursor & Gemini Integration

Nexus exposes its entire agent runtime and tooling to AI code editors via the **Model Context Protocol (MCP)**:

```bash
# Launch Nexus as an MCP server
nexus mcp
```

### Editor Configuration (`.cursor/mcp.json` or `claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "nexus": {
      "command": "nexus",
      "args": ["mcp"],
      "env": {
        "GCP_PROJECT_ID": "your-gcp-project-id"
      }
    }
  }
}
```
Claude Code and Cursor gain native access to all 7 specialist agents, architectural tools, and database schema generators directly within your prompt session.

---

## ⚡ Instant Application Generation: `nexus dream`

Generate complete, runnable applications from natural language:

```bash
nexus dream "I want an app that tracks second-hand luxury watches in Europe with price alerts"
```

```text
--- Nexus Core IT Squad Activated ---
Goal: "I want an app that tracks second-hand luxury watches in Europe with price alerts"
Assignees: Business Analyst, Engineering Manager, UI/UX Designer, Backend Engineer, QA Engineer

=== Project Delivered! ===
App: WatchHub (watchhub)
Tagline: Verified European luxury watch index and real-time deal alerts
Output Directory: ./watchhub
Stories: 4 user stories defined
Cloud Target: GCP (Cloud Run Serverless)
Data Schema: PostgreSQL 16 (4 tables)
UI Component: WatchDashboard.tsx
QA Preflight: PASS (Test suite generated with 100% pre-flight clearance)
```

---

## 🖥️ Local Observability Dashboard: `nexus ui`

Launch the real-time execution dashboard on `http://localhost:8000`:

```bash
nexus ui
```

- **Visual Pipeline**: Real-time status indicators across the 7 specialists.
- **Server-Sent Telemetry**: Live stream of agent thoughts, tool invocations, and model reasoning.
- **Cost & Budget Meter**: Live dollar spend calculation against Gemini 3.8 pricing models.
- **Interactive Wireframe Viewer**: Preview generated HTML mockups and explore generated FastAPI/React code.

---

## 🔄 Stage 1: Closed-Loop Self-Healing

Nexus eliminates "throw-it-over-the-fence" code generation. When the QA Engineer detects failing unit tests or runtime syntax bugs, it automatically triggers a direct feedback loop back to the Full-Stack Engineer with exact traceback diagnostics and failure assertions:

```mermaid
sequenceDiagram
    participant QA as QA Specialist Agent
    participant Runner as Pytest Runner
    participant FS as Full-Stack Engineer Agent
    QA->>Runner: Execute test suite on generated workspace
    alt Tests Pass
        Runner-->>QA: All tests green (100% preflight clearance)
    else Tests Fail
        Runner-->>QA: Capture stacktrace & failed assertions
        QA->>FS: Dispatch healing prompt with exact error context
        FS->>FS: Synthesize surgical code patch
        FS->>Runner: Re-run test suite (Loop up to max_attempts)
        Runner-->>QA: Tests verified green
    end
```

---

## 🔍 Stage 2: Brownfield Legacy Codebase Support

Nexus isn't just for greenfield scaffolding. It analyzes and safely refactors existing enterprise repositories:

### 1. Security & Architecture Audit: `nexus audit`
Scan your existing codebase for secret leaks, unvalidated AI client calls, prompt injection risks, and test coverage drift:
```bash
nexus audit ./existing-repo
```

### 2. AST Blast-Radius Mapping & Surgical Refactoring: `nexus refactor`
Before touching a line of code, Nexus builds an Abstract Syntax Tree (AST) import graph across all files, classes, functions, and FastAPI routes to calculate the exact blast radius:
```bash
nexus refactor "Migrate database pool to PostgreSQL asyncpg" --target src/db/session.py --apply
```
- **Blast Radius Analysis**: Identifies all direct dependents, indirect dependents, and affected REST endpoints.
- **Surgical Patching**: Emits targeted, contract-preserving diffs without blowing away surrounding enterprise logic.

---

## 📊 Stage 3: Team Telemetry & Enterprise ROI: `nexus metrics`

Quantify the exact dollar return on investment (ROI) and DORA velocity acceleration delivered by Nexus across your team:

```bash
nexus metrics ./my-project --hourly-rate 95
```

```text
================================================================================
          NEXUS ENTERPRISE TELEMETRY & ROI SCORECARD: my-project
================================================================================
  Target Path            : /workspace/my-project
  Files / LOC Analyzed   : 116 files | 5,608 lines of code
--------------------------------------------------------------------------------
  FINANCIAL ROI & EFFICIENCY:
  * Human Hours Saved    : 117.6 engineering hours
  * Human Cost Benchmark : $95/hour (Senior Full-Stack benchmark)
  * Gross Value Generated: $11,172.00 USD
  * Total LLM Spend      : $0.0493 USD (415,912 tokens)
  * Net Financial Savings: $11,171.95 USD
  * NET ROI MULTIPLIER   : 226612.0x Return On Investment
--------------------------------------------------------------------------------
  DORA VELOCITY ACCELERATION:
  * Deployment Frequency : 12.0x faster release cadence
  * Lead Time Reduction  : 85.0% decrease from idea to working code
  * Change Failure Rate  : 2.4% (defects intercepted by closed-loop tests)
  * Mean Time to Restore : 3.8 minutes MTTR (automated self-healing loop)
--------------------------------------------------------------------------------
  SECURITY & STABILITY IMPACT:
  * Vulnerabilities Prevented: 17 security defects / secret leaks avoided
  * Closed-Loop Healing Cycles: 9 automated QA repair loops
================================================================================
```

---

## 🛡️ Built-in Cost & Security Guardrails

- **Hard Budget Caps**: Strict `max_budget_usd` ceilings per execution context.
- **Cost-Optimized Model Tiering**: Ultra-fast, highly economical token profile with Gemini 3.8 Flash.
- **Jailbreak Defense**: Pre-flight filters detecting and neutralizing prompt injection attempts.
- **Zero-Leak Secret Scrubbing**: Automated redaction of API keys (`sk-...`, `ghp-...`, private keys) from all logs and telemetry streams.
- **Deterministic Mock Engine**: Run the entire IT pack and test suite locally for \$0.00 using `MockProvider`.

---

## 🧪 Verification & Testing

Nexus includes automated unit tests covering all agents, telemetry contracts, and CLI commands:

```bash
git clone https://github.com/sabburi1994/nexus.git
cd nexus
pytest -o pythonpath=src tests/
```
```text
tests/test_agentic.py ........                                           [ 26%]
tests/test_brownfield.py ....                                            [ 40%]
tests/test_dashboard.py ..                                               [ 46%]
tests/test_it_pack.py ..                                                 [ 53%]
tests/test_nexus.py ......                                               [ 73%]
tests/test_orchestrator.py ..                                            [ 80%]
tests/test_roi_metrics.py ...                                            [ 90%]
tests/test_self_healing.py ...                                           [100%]

======================== 30 passed in 2.27s ========================
```

---

## 🤝 Governance & Feature Requests

Nexus is free for everyone to use, run, and explore. To preserve strict architectural consistency, contracts, and quality gates:

- **Nexus is maintained exclusively by the author.** External pull requests are disabled and will not be accepted.
- **Have an idea or need a feature?** We warmly welcome your feedback! Please submit feature requests, questions, or bug reports via [GitHub Issues](https://github.com/sabburi1994/nexus/issues).

---

## 📄 License
Nexus is licensed under the [Apache 2.0 License](LICENSE).  
Copyright © 2026 Sai Nikhil Abburi. All rights reserved.
