"""Domain-aware ModelProvider driving real Nexus Core IT Squad + ClosedLoopHealer in Showcase."""

from __future__ import annotations

import datetime
import re
from collections.abc import Sequence
from typing import Any, TypeVar

from pydantic import BaseModel

from nexus.ai.pricing import calculate_cost_usd
from nexus.brownfield.analyzer import BlastRadiusResult
from nexus.brownfield.refactor import FilePatch, RefactorPlan
from nexus.maintenance.healer import DiagnosisResult
from nexus.providers.base import BaseModelProvider, ModelResponse
from nexus.teams.it_pack.ba import ProductProposal
from nexus.teams.it_pack.data_architect import DataArchitecture
from nexus.teams.it_pack.designer import UiSpecification
from nexus.teams.it_pack.devops import DevopsSpecification
from nexus.teams.it_pack.fullstack import FullStackSpecification
from nexus.teams.it_pack.qa import QaSpecification
from nexus.teams.it_pack.solution_architect import SolutionBlueprint

T = TypeVar("T", bound=BaseModel)


class ShowcaseSquadProvider(BaseModelProvider):
    """
    Executes real Nexus Core IT Squad agents deterministically for public sandbox runs.
    Tracks per-agent token budgets and optionally simulates an initial QA preflight defect
    so ClosedLoopHealer runs an authentic diagnosis -> patch -> retest cycle.
    """

    def __init__(self, idea: str, target_cloud: str = "gcp", simulate_healing: bool = True) -> None:
        self.idea = idea.strip()
        self.target_cloud = target_cloud.lower()
        self.simulate_healing = simulate_healing
        self.calls: list[dict[str, Any]] = []
        self._qa_invocations = 0
        self._healed_backend = False
        self._slug, self._title = self._derive_identity(self.idea)
        self._table_prefix = self._slug.replace("-", "_")

    @property
    def name(self) -> str:
        return "showcase-deterministic"

    @staticmethod
    def _derive_identity(idea: str) -> tuple[str, str]:
        words = re.findall(r"[A-Za-z0-9]+", idea)
        stop = {
            "i",
            "want",
            "an",
            "app",
            "application",
            "that",
            "builds",
            "to",
            "for",
            "with",
            "and",
            "the",
            "a",
            "of",
            "in",
            "on",
        }
        keywords = [w for w in words if w.lower() not in stop][:4]
        if not keywords:
            keywords = words[:3] or ["nexus", "service"]
        slug = "-".join(k.lower() for k in keywords)[:32].strip("-") or "nexus-service"
        title = " ".join(k.capitalize() for k in keywords[:3])
        if len(title) < 4:
            title = "Nexus Generated Workspace"
        return slug, title

    def _record(
        self,
        agent_name: str,
        role: str,
        prompt: str,
        output_text: str,
        summary: str,
        artifact_preview: str,
        status: str = "completed",
    ) -> None:
        in_tok = max(120, len(prompt.split()) * 4 + 90)
        out_tok = max(140, len(output_text.split()) * 2 + 120)
        cost = calculate_cost_usd(in_tok, out_tok, model="gemini-3.8-flash")
        now = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=len(self.calls) * 2)
        self.calls.append(
            {
                "agentName": agent_name,
                "role": role,
                "status": status,
                "costUsd": round(cost, 6),
                "tokens": in_tok + out_tok,
                "inputTokens": in_tok,
                "outputTokens": out_tok,
                "summary": summary,
                "timestamp": now.strftime("%H:%M:%S"),
                "artifactPreview": artifact_preview,
            }
        )

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> ModelResponse:
        reply = f"Synthesized guidance for {self._title}: enforce strict schema validation and telemetry middleware."
        return ModelResponse(
            text=reply,
            input_tokens=max(40, len(prompt.split()) * 2),
            output_tokens=max(20, len(reply.split()) * 2),
            cost_usd=0.0,
            model="gemini-3.8-flash",
        )

    def converse(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> ModelResponse:
        return self.generate(str(messages))

    def structured(
        self,
        prompt: str,
        response_model: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> T:
        if response_model is ProductProposal:
            proposal = self._build_proposal()
            self._record(
                "Business Analyst",
                "Requirements Engineer",
                prompt,
                proposal.model_dump_json(),
                f"Deconstructed prompt into '{proposal.title}' ({proposal.app_name}) with {len(proposal.user_stories)} stories and HTML wireframe.",
                "docs/preview_mockup.html",
            )
            return proposal  # type: ignore[return-value]

        if response_model is SolutionBlueprint:
            blueprint = self._build_solution()
            self._record(
                "Solution Architect",
                "System Topology",
                prompt,
                blueprint.model_dump_json(),
                f"Locked {blueprint.cloud_provider.upper()} {blueprint.compute_pattern} across {len(blueprint.integration_services)} cloud primitives.",
                "docs/ARCHITECTURE.md",
            )
            return blueprint  # type: ignore[return-value]

        if response_model is DataArchitecture:
            data = self._build_data_arch()
            self._record(
                "Data Architect",
                "Relational Schemas",
                prompt,
                data.model_dump_json(),
                f"Modeled {len(data.tables)} normalized tables ({', '.join(data.tables)}) with PostgreSQL UUID keys & indexes.",
                "docs/DATA_ARCHITECTURE.md",
            )
            return data  # type: ignore[return-value]

        if response_model is UiSpecification:
            ui = self._build_ui()
            self._record(
                "UI/UX Designer",
                "Platform Design System",
                prompt,
                ui.model_dump_json(),
                f"Bound @nexus-agent-framework/ui paper components into {ui.component_name}.tsx.",
                "frontend/src/App.tsx",
            )
            return ui  # type: ignore[return-value]

        if response_model is FullStackSpecification:
            is_healing = "closed-loop self-healing" in prompt.lower()
            if is_healing:
                self._healed_backend = True
            spec = self._build_fullstack(healed=not self.simulate_healing or self._healed_backend)
            self._record(
                "Full-Stack Engineer" if not is_healing else "Full-Stack Engineer (Patch)",
                "Application Synthesis" if not is_healing else "Surgical Code Repair",
                prompt,
                spec.model_dump_json(),
                (
                    "Patched Pydantic bounds, /ready health probe, and GuardrailManager input inspection."
                    if is_healing
                    else f"Compiled FastAPI create_nexus_app() microservice + React client for '{self._slug}'."
                ),
                "backend/src/main.py",
            )
            return spec  # type: ignore[return-value]

        if response_model is DevopsSpecification:
            devops = self._build_devops()
            self._record(
                "DevOps Engineer",
                "Infrastructure as Code",
                prompt,
                devops.model_dump_json(),
                f"Emitted Terraform IaC for {self.target_cloud.upper()}, least-privilege IAM, and docker-compose.yml.",
                "infra/terraform/main.tf",
            )
            return devops  # type: ignore[return-value]

        if response_model is QaSpecification:
            self._qa_invocations += 1
            qa = self._build_qa(passed=self._healed_backend or not self.simulate_healing)
            self._record(
                "QA & Security Engineer",
                "Preflight Gate",
                prompt,
                qa.model_dump_json(),
                qa.security_verdict,
                "backend/tests/test_api.py",
                status="completed" if qa.passed_preflight else "error",
            )
            return qa  # type: ignore[return-value]

        if response_model is DiagnosisResult:
            diag = DiagnosisResult(
                root_cause="Preflight gate detected missing Pydantic positivity check (amount >= 0) and missing GuardrailManager input check in create endpoint.",
                suggested_fix="Add GuardrailManager().inspect_input() before model invocation and expose /api/v1/items readiness validation.",
                is_transient=False,
                confidence=0.96,
            )
            self._record(
                "Autonomous Healer",
                "Root-Cause Diagnosis",
                prompt,
                diag.model_dump_json(),
                f"Diagnosed preflight failure (confidence {int(diag.confidence * 100)}%): dispatched surgical diff to Full-Stack Engineer.",
                "healing_report.json",
            )
            return diag  # type: ignore[return-value]

        if response_model is RefactorPlan:
            return RefactorPlan(  # type: ignore[return-value]
                task="Harden AI dispute calls with GuardrailManager & externalize secret",
                target_files=["config.py", "ai_triage.py"],
                blast_radius=BlastRadiusResult(target="models.py", risk_tier="MEDIUM"),
                patches=[
                    FilePatch(
                        file_path="config.py",
                        change_type="modify",
                        diff_or_content='- LEGACY_GATEWAY_KEY = "sk-demo..."\n+ LEGACY_GATEWAY_KEY = os.environ["LEGACY_GATEWAY_KEY"]',
                    ),
                    FilePatch(
                        file_path="ai_triage.py",
                        change_type="modify",
                        diff_or_content='+ from nexus.security import GuardrailManager\n+ safe_note = GuardrailManager().inspect_input(customer_note)\n- prompt = f"Classify dispute...: {customer_note}"\n+ prompt = f"Classify dispute...: {safe_note}"',
                    ),
                ],
                verification_strategy="Run pytest verification across routes.py dependent endpoints without altering CustomerAccount or InvoiceRecord wire schemas.",
                estimated_risk="LOW - AST confirms InvoiceRecord signature unchanged; 2 dependent modules patched cleanly.",
            )

        raise ValueError(f"Unsupported structured response model in showcase: {response_model}")

    def _build_proposal(self) -> ProductProposal:
        wireframe = (
            f"<div style=\"font-family:'Plus Jakarta Sans',sans-serif;background:#f5f1e8;color:#172a2e;padding:24px;border:1px solid #d4ccc0;border-radius:8px\">"
            f"<div style='display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #d4ccc0;padding-bottom:12px;margin-bottom:16px'>"
            f"<strong style='font-size:18px'>{self._title}</strong>"
            f"<span style='font-family:monospace;font-size:11px;background:#e6f4ee;color:#0f7657;padding:4px 8px;border:1px solid #9ec9b8;border-radius:4px'>Gemini 3.8 · Guarded</span>"
            f"</div>"
            f"<p style='font-size:13px;color:#47534e;margin:0 0 16px'>Scoped from: {self.idea[:140]}</p>"
            f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:10px'>"
            f"<div style='background:#fffdf8;border:1px solid #d4ccc0;padding:12px;border-radius:6px'><small style='color:#64748b'>TRACKED RECORDS</small><div style='font-size:20px;font-weight:700;margin-top:4px'>1,284</div></div>"
            f"<div style='background:#fffdf8;border:1px solid #d4ccc0;padding:12px;border-radius:6px'><small style='color:#64748b'>PREFLIGHT GATE</small><div style='font-size:20px;font-weight:700;color:#0f7657;margin-top:4px'>100%</div></div>"
            f"<div style='background:#fffdf8;border:1px solid #d4ccc0;padding:12px;border-radius:6px'><small style='color:#64748b'>CLOUD TARGET</small><div style='font-size:20px;font-weight:700;margin-top:4px'>{self.target_cloud.upper()}</div></div>"
            f"</div></div>"
        )
        return ProductProposal(
            app_name=self._slug,
            title=self._title,
            tagline=f"Auditable, guardrail-protected service synthesized for: {self.idea[:72]}",
            target_audience="Platform Engineering & Operations Teams",
            user_stories=[
                f"As an operator of {self._title}, I want structured ingestion and audit logging so every action is traceable.",
                "As a platform engineer, I want Pydantic-validated FastAPI endpoints with /health and /ready probes.",
                "As a security lead, I want prompt injection blocking and automatic credential redaction enforced before model execution.",
                "As a DevOps engineer, I want reproducible Terraform serverless deployment definitions out of the box.",
            ],
            core_features=[
                "FastAPI create_nexus_app() runtime with correlation headers",
                "PostgreSQL + SQLAlchemy NexusEntity persistence layer",
                "React workspace powered by @nexus-agent-framework/ui",
                "GuardrailManager prompt shield & zero-leak logging",
            ],
            ui_concept="Editorial paper-and-ink workspace with tabular telemetry KPIs and live record explorer",
            wireframe_preview_html=wireframe,
        )

    def _build_solution(self) -> SolutionBlueprint:
        cloud: Any = self.target_cloud if self.target_cloud in ("gcp", "aws", "local") else "gcp"
        services = (
            ["Google Cloud Run v2", "Vertex AI (gemini-3.8-flash)", "Secret Manager", "Cloud SQL PostgreSQL 16"]
            if cloud == "gcp"
            else ["AWS App Runner / Fargate", "Amazon RDS PostgreSQL", "Secrets Manager", "Vertex AI Gateway"]
            if cloud == "aws"
            else ["Local Uvicorn FastAPI", "PostgreSQL Docker Service", "MockProvider Zero-Cost Engine"]
        )
        return SolutionBlueprint(
            cloud_provider=cloud,
            compute_pattern=f"{cloud.upper()} Serverless Container (scale 0..5)",
            system_topology="React (@nexus-agent-framework/ui) -> FastAPI Gateway (GuardrailManager) -> Async SQLAlchemy + Vertex AI Gemini 3.8",
            non_functional_requirements=[
                "Strict budget cap enforcement per tenant/run",
                "Zero plaintext secrets in environment or logs",
                "Sub-200ms p95 API validation latency",
            ],
            integration_services=services,
        )

    def _build_data_arch(self) -> DataArchitecture:
        tbl = self._table_prefix
        ddl = (
            f"CREATE TABLE {tbl}_records (\n"
            "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "  title VARCHAR(140) NOT NULL,\n"
            "  status VARCHAR(32) NOT NULL DEFAULT 'verified',\n"
            "  score NUMERIC(6,2) NOT NULL DEFAULT 0.00,\n"
            "  created_at TIMESTAMPTZ NOT NULL DEFAULT now()\n"
            ");\n\n"
            f"CREATE INDEX idx_{tbl}_status ON {tbl}_records(status);"
        )
        return DataArchitecture(
            database_engine="PostgreSQL 16 (asyncpg)",
            tables=[f"{tbl}_records", f"{tbl}_audit_events"],
            relationships=[f"{tbl}_records 1:N {tbl}_audit_events"],
            indexes=[f"idx_{tbl}_status", f"idx_{tbl}_created_at"],
            sql_ddl_schema=ddl,
        )

    def _build_ui(self) -> UiSpecification:
        comp_name = "".join(part.capitalize() for part in self._slug.split("-")) + "Workspace"
        react_code = f"""import React from "react";
import {{ NexusHeader, StatCard, SecurityShieldBadge, TraceViewer }} from "@nexus-agent-framework/ui";

export default function {comp_name}() {{
  return (
    <div className="min-h-screen bg-[#f5f1e8] text-[#172a2e]">
      <NexusHeader appName="{self._title}" tagline="Delivered by Nexus Virtual IT Squad" />
      <main className="mx-auto max-w-6xl space-y-6 p-6">
        <SecurityShieldBadge injectionsBlocked={{0}} piiScrubbed={{0}} />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <StatCard title="Service Health" value="100%" trend="up" trendValue="Ready" accent="emerald" />
          <StatCard title="Model Tier" value="Gemini 3.8" subtitle="Flash Serverless" accent="cobalt" />
          <StatCard title="Cost Guardrail" value="$1.00/day" subtitle="Enforced cap" accent="terracotta" />
        </div>
      </main>
    </div>
  );
}}
"""
        return UiSpecification(
            component_name=comp_name,
            color_palette="Editorial Paper (#f5f1e8) & Slate-Teal Ink (#172a2e) with Terracotta (#bd513d)",
            react_code=react_code,
        )

    def _build_fullstack(self, healed: bool) -> FullStackSpecification:
        if not healed:
            main_py = f'''"""Generated backend service (Initial QA pass detected missing guardrail & input bounds)."""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="{self._title}", version="0.1.0")

class RecordInput(BaseModel):
    name: str
    score: float  # DEFECT: missing ge=0 validation & GuardrailManager sanitization

@app.get("/health")
def health() -> dict[str, str]:
    return {{"status": "ok"}}

@app.post("/api/v1/records")
def create_record(item: RecordInput) -> dict[str, object]:
    return {{"created": True, "name": item.name, "score": item.score}}
'''
        else:
            main_py = f'''"""Generated backend service for {self._title} (Closed-Loop Healed & Preflight Verified)."""
from fastapi import HTTPException
from pydantic import BaseModel, Field

from nexus.api import create_nexus_app
from nexus.security import GuardrailManager, SecurityViolationError

app, _ = create_nexus_app(title="{self._title}", version="1.0.0")
guardrail = GuardrailManager()

class RecordInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=140)
    score: float = Field(default=0.0, ge=0.0, le=100.0)

@app.post("/api/v1/records")
def create_record(item: RecordInput) -> dict[str, object]:
    try:
        clean_name = guardrail.inspect_input(item.name)
    except SecurityViolationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {{"created": True, "name": clean_name, "score": item.score, "healed": True}}
'''

        models_py = f'''"""SQLAlchemy & Pydantic schemas for {self._title}."""
from pydantic import BaseModel, Field
from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from nexus.db import NexusEntity


class ServiceRecord(NexusEntity):
    __tablename__ = "{self._table_prefix}_records"

    name: Mapped[str] = mapped_column(String(140), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class RecordSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=140)
    score: float = Field(default=0.0, ge=0.0, le=100.0)
'''

        frontend_tsx = self._build_ui().react_code
        api_client = f"""export interface RecordPayload {{
  name: string;
  score: number;
}}

export async function createServiceRecord(payload: RecordPayload) {{
  const res = await fetch("/api/v1/records", {{
    method: "POST",
    headers: {{ "Content-Type": "application/json" }},
    body: JSON.stringify(payload),
  }});
  if (!res.ok) throw new Error("Failed to save record for {self._slug}");
  return res.json();
}}
"""
        return FullStackSpecification(
            backend_main_py=main_py,
            backend_models_py=models_py,
            frontend_app_tsx=frontend_tsx,
            frontend_api_client_ts=api_client,
        )

    def _build_devops(self) -> DevopsSpecification:
        slug = self._slug
        tf_main = f"""terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 5.0"
    }}
  }}
}}

resource "google_cloud_run_v2_service" "{slug.replace("-", "_")}" {{
  name     = "{slug}"
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {{
    scaling {{
      min_instance_count = 0
      max_instance_count = 5
    }}
    containers {{
      image = "europe-west1-docker.pkg.dev/${{var.gcp_project_id}}/nexus/{slug}:latest"
      resources {{
        limits = {{
          cpu    = "1000m"
          memory = "512Mi"
        }}
      }}
    }}
  }}
}}
"""
        tf_vars = """variable "gcp_project_id" {
  type = string
}

variable "gcp_region" {
  type    = string
  default = "europe-west1"
}
"""
        compose = f"""services:
  api:
    build: ./backend
    ports:
      - "8080:8080"
    environment:
      - SERVICE_NAME={slug}
"""
        ci = """name: Deploy Nexus Service
on:
  push:
    branches: [main]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest backend/tests/
"""
        return DevopsSpecification(
            cloud_target=self.target_cloud,
            terraform_main_tf=tf_main,
            terraform_variables_tf=tf_vars,
            docker_compose_yml=compose,
            ci_cd_workflow_yml=ci,
        )

    def _build_qa(self, passed: bool) -> QaSpecification:
        test_code = '''"""Preflight pytest verification generated by Nexus QA Engineer."""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_and_readiness() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_record_validation() -> None:
    bad = client.post("/api/v1/records", json={"name": "valid", "score": -15})
    assert bad.status_code == 422
'''
        if not passed:
            return QaSpecification(
                test_suite_code=test_code,
                security_verdict="FAIL: Preflight caught missing ge=0 validation on score and missing GuardrailManager input check.",
                passed_preflight=False,
            )
        return QaSpecification(
            test_suite_code=test_code,
            security_verdict="PASS: All routes validated, GuardrailManager injection shield verified, and Pydantic bounds enforced.",
            passed_preflight=True,
        )
