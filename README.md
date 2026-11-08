# Nexus: Orchestrator-Native AI Agentic Framework

> The **AI Agentic Framework** that equips non-technical creators with a full virtual IT department while interfacing natively with **Claude Code, Cursor, Codex, and Gemini** via the Model Context Protocol (MCP).

Nexus bridges the gap between raw ideas and production code. It serves two distinct developer cohorts:
1. **Beginners with Ideas**: Run `nexus dream "<vague idea>"` and the **Core IT Pack** (BA, Product Manager, UI Designer, Backend Engineer, and QA) takes the idea, designs the UI mockup, writes the sprint plan, generates the backend code, and runs tests.
2. **AI Orchestrator Users (Claude Code, Cursor, Codex, Gemini)**: Run `nexus mcp` to expose your agents, tools, databases, and guardrails to any modern AI IDE as first-class, equal participants.

---

## 🏢 The Nexus Core IT Pack

Nexus comes pre-packaged with an autonomous IT squad that simulates a real-world software engineering organization:

```mermaid
flowchart TD
    User["Creator with an Idea<br/>(Vague Requirements)"] --> BA["1. Business Analyst<br/>(User Stories & Scope)"]
    BA --> SA["2. Solution Architect<br/>(System Topology & Cloud Choice)"]
    SA --> DA["3. Data Architect<br/>(ERD & SQL Schema)"]
    DA --> Design["4. UI/UX Designer<br/>(Design Tokens & Wireframe)"]
    Design & DA --> FS["5. Full-Stack Engineer<br/>(React UI + FastAPI Backend)"]
    SA & DA --> DevOps["6. DevOps Engineer<br/>(Terraform IaC for target cloud)"]
    FS & DevOps --> QA["7. QA & Security Engineer<br/>(Preflight Guardrails & Test Suite)"]
    QA --> Repo["Delivered Application Workspace<br/>(Runnable Full-Stack Project on Disk)"]
```

### 1. Business Analyst (`BusinessAnalystAgent`)
Takes conversational, incomplete user thoughts and formats them into a crisp **Product Proposal**:
- Canonical app slug & value proposition tagline.
- User stories (`As a [user], I want to [action] so that [benefit]`).
- Core features specification & HTML wireframe preview.

### 2. Solution Architect (`SolutionArchitectAgent`)
Evaluates holistic system design, integration boundaries, and non-functional requirements:
- Selects the cloud runtime strategy (GCP, AWS, or Local).
- Defines compute model (Cloud Run serverless container vs VM).
- Details service communication topology.

### 3. Data Architect (`DataArchitectAgent`)
Designs the relational and persistence architecture:
- Normalizes tables, foreign keys, and indexes.
- Emits clean, production-ready PostgreSQL SQL DDL schemas.

### 4. UI/UX Designer (`UiDesignerAgent`)
Focuses on user journey, design tokens, and interactive mockups styled with Tailwind CSS and `@nexus/ui`.

### 5. Full-Stack Engineer (`FullStackEngineerAgent`)
Implements the unified end-to-end codebase:
- Production-grade FastAPI microservice with Gemini 3.8 client.
- Pydantic models & SQLAlchemy entity definitions.
- React frontend consuming the API endpoints.

### 6. DevOps Engineer (`DevopsEngineerAgent`)
Generates real Infrastructure as Code (IaC) tailored to the architectural need and selected cloud:
- Complete Terraform `main.tf` and `variables.tf` (e.g. Cloud Run, IAM `roles/aiplatform.user`, Secret Manager).
- Multi-container `docker-compose.yml` for local development.
- GitHub Actions CI/CD deployment pipeline.

### 7. QA & Security Engineer (`QaEngineerAgent`)
Runs pre-flight security checks (injection shields, permission levels) and produces an executable `pytest` test suite.

---

## 🔌 Orchestrator-Native: Claude Code & Cursor Integration

Nexus is designed to work as an equal peer alongside **Claude Code, Cursor, Codex, and Gemini CLI**:

```bash
# Start the Nexus Model Context Protocol (MCP) server
nexus mcp
```

### Connecting from Cursor / Claude Code
Add Nexus to your `.cursor/mcp.json` or `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "nexus": {
      "command": "python",
      "args": ["-m", "nexus.cli.main", "mcp"],
      "env": {
        "GCP_PROJECT_ID": "finhub-510316"
      }
    }
  }
}
```
Instantly, Claude Code or Cursor gains access to all Nexus tools, allowing you to trigger IT squad workflows, check AI connections, or diagnose errors right inside your editor prompt.

---

## 🖥️ Localhost Visualizer & Agent Observability (`nexus ui`)

Nexus provides a built-in interactive web visualizer to track your agent squad and execution telemetry in real time:

```bash
# Launch localhost progress visualizer on http://localhost:8000
nexus ui
```

### Features:
- **Visual Squad Pipeline**: Live status indicators for each agent (`Idle`, `Active`, `Done ✓`) as tasks move from BA to Manager, Designer, Engineer, and QA.
- **Real-Time Telemetry Stream**: Server-Sent Events (SSE) feed displaying thoughts, tool calls, and model reasoning.
- **Cost & Budget Meter**: Live dollar spend tracking (`total_cost_usd`) updated after every inference turn.
- **Live Artifact Inspector**: Read generated Product Proposals, preview interactive HTML wireframes, and inspect React/FastAPI code directly in your browser.
- **Interactive Launcher**: Trigger new squad builds (`Run IT Squad`) directly from the web interface.

---

## 🚀 Instant Application Creation: `nexus dream`

```bash
nexus dream "I want an app that tracks second-hand luxury watches in Europe with price alerts"
```

Output:
```text
--- Nexus Core IT Squad Activated ---
Goal: "I want an app that tracks second-hand luxury watches in Europe with price alerts"
Assignees: Business Analyst, Engineering Manager, UI/UX Designer, Backend Engineer, QA Engineer

=== Project Delivered! ===
App: WatchHub (watchhub)
Tagline: Verified European luxury watch index and real-time deal alerts
Output Directory: ./watchhub
Tasks: 6 sprint tasks defined
UI Component: WatchDashboard.tsx
QA Status: PASS (Test suite generated with 100% pre-flight clearance)
```

---

## 🛡️ Built-in Cost & Security Guardrails

- **Zero Runaway Bills**: `max_budget_usd` spend ceilings on every agent execution context.
- **Gemini 3.8 Flash Cost Profile**: \$0.075 / \$0.30 per million tokens (cents per month for active squads).
- **Prompt Injection Defense**: Intercepts jailbreaks (`"ignore all prior instructions"`) before hitting the LLM.
- **PII & Secret Scrubber**: Redacts API keys (`sk-...`, `ghp-...`) and credentials automatically.
- **Zero-Cost Mock Engine**: Run the entire IT pack and test suite locally for \$0.00 using `MockProvider`.

---

## Repository Map

```text
nexus/
├── src/nexus/
│   ├── orchestrator/           # Embedded MCP server & protocol bridges (Claude, Cursor, Gemini)
│   ├── teams/it_pack/          # Core IT Pack (BA, Manager, Designer, Engineer, QA)
│   ├── agents/                 # BaseAgent, AgentContext, multi-turn reasoning
│   ├── tools/                  # @tool decorator & ToolPermission (READ_ONLY, MUTATION, CRITICAL)
│   ├── providers/              # Vertex AI (Gemini 3.8 Flash), MockProvider, Ollama
│   ├── security/               # Injection shield, credential sanitizer, tool guardrails
│   ├── maintenance/            # AutonomousHealer: AI root-cause diagnosis & repair
│   ├── qa/                     # LLMJudge: Autonomous evaluation & faithfulness verification
│   ├── api/                    # Standardized microservice factory & telemetry
│   ├── db/                     # Async PostgreSQL connection pooling & base entities
│   ├── scraping/               # Resilient rate-limited crawler & backoff engine
│   └── cli/                    # CLI tools (`nexus dream`, `nexus mcp`, `nexus check-ai`)
├── packages/
│   └── ui/                     # Shared React + Tailwind agentic UI (@nexus/ui)
├── infra/
│   └── terraform/modules/      # Reusable Terraform infrastructure modules
└── tests/                      # Automated test suite (18 passing)
```

---

## Verification

```bash
git clone https://github.com/sabburi1994/nexus.git
cd nexus
pytest tests/
```
