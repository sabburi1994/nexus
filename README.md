# Nexus: Autonomous AI Agentic Framework

> An open, production-grade **AI Agentic Framework** designed for autonomous agent execution, self-healing maintenance, security guardrails, and automated evaluation.

Nexus is built for engineering teams that have a clear product vision but lack deep infrastructure, security, or agent plumbing. It eliminates the fragile glue code required to build autonomous systems by providing **first-class agent primitives, cost guardrails, and self-maintaining tool loops**.

---

## Why Nexus?

| Traditional AI Libraries (LangChain, CrewAI) | Traditional Web Frameworks (Next.js, FastAPI) | **Nexus Agentic Framework** |
| :--- | :--- | :--- |
| Fragmented abstractions & breaking changes | No concept of agent loops or non-determinism | **Unified full-stack agent lifecycle** |
| Runaway token costs & surprise bills | Unaware of LLM spend | **Hard budget caps (`max_budget_usd`) on every agent** |
| Blind tool execution without sandboxing | Manual RBAC on endpoints | **Tool permissions (`READ_ONLY`, `MUTATION`, `CRITICAL`)** |
| Vulnerable to prompt injection | Only standard SQL/XSS defenses | **Pre-flight adversarial injection & PII scrubbing** |
| Manual debugging & brittle maintenance | Standard stack traces | **`AutonomousHealer`: AI diagnoses root cause & fixes** |
| Probabilistic test flakiness | Deterministic assertions only | **`LLMJudge`: Autonomous faithfulness & safety evals** |

---

## Architecture

```text
nexus/
├── src/nexus/
│   ├── agents/                 # BaseAgent, AgentContext, multi-turn reasoning
│   ├── tools/                  # @tool decorator with automatic schema inference
│   ├── providers/              # Pluggable backends: Vertex AI (Gemini 3.8), Mock, Ollama
│   ├── security/               # Prompt injection shield, PII scrubber, tool guardrails
│   ├── maintenance/            # AutonomousHealer: self-healing bug diagnosis
│   ├── qa/                     # LLMJudge: Autonomous evaluation & faithfulness verification
│   ├── api/                    # Standardized microservice factory & telemetry
│   ├── db/                     # Async PostgreSQL connection pooling & base entities
│   ├── scraping/               # Resilient rate-limited crawler & backoff engine
│   └── cli/                    # CLI tools (`nexus check-ai`, `nexus new <app>`)
├── packages/
│   └── ui/                     # Shared React + Tailwind agentic UI (@nexus/ui)
├── infra/
│   └── terraform/modules/      # Reusable Terraform infrastructure modules
└── tests/                      # Automated test suite (14 passing)
```

---

## 1. Quick Example: Creating an Autonomous Agent

```python
from nexus.agents import BaseAgent
from nexus.providers.vertex import VertexAIProvider
from nexus.tools import tool, ToolPermission

# Define safe, permission-governed tools
@tool(name="fetch_stock_price", permission=ToolPermission.READ_ONLY)
def fetch_stock_price(ticker: str) -> dict[str, float]:
    """Fetch real-time stock price from market exchange."""
    return {ticker: 185.50}

# Instantiate agent with hard safety ceiling
agent = BaseAgent(
    name="MarketAnalyst",
    system_prompt="You are a market intelligence agent. Use tools to look up real facts.",
    provider=VertexAIProvider(default_model="gemini-3.8-flash"),
    tools=[fetch_stock_price],
    max_budget_usd=0.05,  # Prevents runaway spend (max 5 cents per run)
)

result = agent.run("What is the current price of AAPL?")
print(result.output)
print(f"Cost: ${result.total_cost_usd:.6f}")
```

---

## 2. AI-Enabled Security: Injection Shield & PII Sanitizer

Nexus inspects all prompts **before** sending tokens to the LLM:
- **Prompt Injection Defense**: Blocks jailbreaks (`"ignore all previous instructions"`) with `SecurityViolationError`.
- **Zero-Leak Sanitizer**: Redacts API keys (`sk-...`), GitHub tokens, and sensitive PII before model ingestion.
- **Tool Governance**: Enforces affirmative authorization before any `CRITICAL` tool is executed.

---

## 3. Zero-Cost Testing & Development

Never burn money while developing or running CI/CD:
```python
from nexus.providers.mock import MockProvider
from nexus.agents import BaseAgent

# 100% free local development or CI pipeline
test_agent = BaseAgent(
    name="TestAgent",
    system_prompt="...",
    provider=MockProvider(default_reply="Task completed."),
)
```

---

## 4. AI-Enabled Maintenance: `AutonomousHealer`

When an unhandled exception or agent tool failure occurs, the `AutonomousHealer` diagnoses the root cause and generates a remediation plan:

```python
from nexus.maintenance import AutonomousHealer
from nexus.providers.vertex import VertexAIProvider

healer = AutonomousHealer(provider=VertexAIProvider())
diagnosis = healer.diagnose_failure(
    error_message="ZeroDivisionError: division by zero",
    stack_trace="...",
    context_snippet="def calc_ratio(a, b): return a / b",
)

print(diagnosis.root_cause)      # "ZeroDivisionError when denominator b is 0"
print(diagnosis.suggested_fix)   # "Add `if b == 0: return 0.0` guard check"
```

---

## 5. AI-Enabled QA: `LLMJudge`

Nexus includes autonomous evaluation to grade agent answers without manual human labeling:

```python
from nexus.qa import LLMJudge
from nexus.providers.vertex import VertexAIProvider

judge = LLMJudge(provider=VertexAIProvider())
score = judge.evaluate(
    task="Calculate the P/E ratio for NVDA given EPS of 4.0 and price of 120",
    agent_output="The P/E ratio is 30.0.",
    reference_facts="Price: 120, EPS: 4.0, P/E = 120 / 4 = 30",
)

print(f"Passed: {score.passed}, Faithfulness: {score.faithfulness_score}")
```

---

## Getting Started

```bash
git clone https://github.com/sabburi1994/nexus.git
cd nexus
pytest tests/
```
