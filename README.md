# Nexus Platform Framework

> Autonomous Application & Platform Framework powered by **Google Cloud Vertex AI** and **Gemini 3.8 Flash**.

`nexus` is the foundation framework for building, deploying, and operating domain applications (such as FinHub, Kalssesall, Predictive Economics, JobRadar, and CivicSignal). It unifies AI orchestration, scraping pipelines, database persistence, shared UI design systems, and Infrastructure as Code into a single standard.

---

## Architecture Overview

```text
nexus/
├── pyproject.toml              # Python framework package (uv / pip)
├── src/nexus/
│   ├── ai/                     # Gemini 3.8 + Vertex AI SDK (IAM OAuth, schemas, tools)
│   ├── api/                    # Standardized FastAPI application factory & telemetry
│   ├── db/                     # Async PostgreSQL connection pooling & base entities
│   ├── scraping/               # Resilient rate-limited crawler & backoff engine
│   └── cli/                    # CLI for scaffolding apps (`nexus new`) & verification
├── packages/
│   └── ui/                     # Shared React + Tailwind component library (@nexus/ui)
├── infra/
│   └── terraform/modules/      # Reusable GCP Terraform modules (IAM, Vertex AI, Cloud Run)
└── tests/                      # Automated test suite
```

---

## Core Capabilities

### 1. Unified Gemini 3.8 Vertex AI Client (`nexus.ai`)
- **Direct GCP IAM Auth**: Uses VM instance metadata or `gcloud` OAuth bearer tokens (`roles/aiplatform.user`) with 40-minute in-memory caching. No hardcoded or leaked API keys.
- **Global Endpoint Routing**: Automatically targets Google Cloud's `global` publisher endpoint for Gemini 3.8 Flash.
- **Thinking Configuration**: Built-in support for Gemini 3.8 reasoning (`thinkingLevel: "low"`).
- **Structured Schema Extraction**: Constrained JSON generation directly into typed Pydantic models.
- **Multimodal Document Understanding**: Native support for inline PDF/image base64 ingestion.
- **Multi-Turn Tool Loops**: Autonomous tool dispatching with zero numerical hallucinations.
- **Cost Tracking**: Accurate Vertex AI token pricing calculations ($0.075 / $0.30 per million tokens).

```python
from nexus.ai import GeminiClient
from pydantic import BaseModel

class FinancialReport(BaseModel):
    sentiment: str
    key_drivers: list[str]

client = GeminiClient(project_id="finhub-510316")
report: FinancialReport = client.structured(
    prompt="Analyze the latest ECB rate decision.",
    response_model=FinancialReport,
)
```

### 2. Standardized Microservice Factory (`nexus.api`)
- Automatic telemetry headers (`X-Request-ID`, `X-Process-Time`).
- Safe CORS defaults.
- Built-in `/health` and `/ready` probes.
- Consistent JSON error formatting.

```python
from nexus.api import create_nexus_app

app = create_nexus_app(title="JobRadar", version="1.0.0")
```

### 3. Asynchronous Database Persistence (`nexus.db`)
- UUID primary keys and automated UTC `created_at` / `updated_at` timestamps (`NexusEntity`).
- Asynchronous session management with connection pool pre-pinging.

### 4. Resilient Scraping Engine (`nexus.scraping`)
- Configurable rate limiting and jitter delays.
- User-Agent rotation.
- Exponential backoff on HTTP 429 and 5xx errors.

### 5. Shared Design System (`@nexus/ui`)
- React + Tailwind components (`StatCard`, `AiBadge`, `MetricTrend`) shared across all domain frontends.

### 6. Infrastructure as Code (`infra/terraform`)
- Reusable Terraform modules provisioning GCP baseline services, service accounts with `roles/aiplatform.user`, and Secret Manager access.

---

## CLI Usage

### Verify Gemini 3.8 Connectivity
```bash
nexus check-ai --model gemini-3.8-flash --project finhub-510316
```

### Scaffold a New Application
```bash
nexus new myapp
```
Creates a complete, runnable microservice configured with the Nexus framework, Gemini 3.8 client, FastAPI routes, tests, and Dockerfile.

---

## Testing

```bash
pytest tests/
```
