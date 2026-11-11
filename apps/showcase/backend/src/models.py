"""Showcase Data Models & API Schemas using NexusEntity and Pydantic."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from nexus.db import NexusEntity


class AnalysisReport(NexusEntity):
    """Persisted market intelligence report."""

    __tablename__ = "analysis_reports"

    target_name: Mapped[str] = mapped_column(String(120), nullable=False)
    sector: Mapped[str] = mapped_column(String(60), nullable=False, default="Macro")
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    summary: Mapped[str] = mapped_column(Text, nullable=False)


class ScanRequest(BaseModel):
    target: str = Field(..., min_length=2, max_length=240, description="Entity or macro indicator to analyze")
    sector: str = Field("Macro", description="Economic sector or asset class")


class ScanResponse(BaseModel):
    id: str
    target: str
    sector: str
    sentiment_score: float
    risk_level: str
    summary: str
    model: str = "gemini-3.8-flash"
    tokens_used: int = 0


class SimulationRequest(BaseModel):
    idea: str = Field(..., min_length=4, max_length=1200, description="Application requirement or prompt to simulate")
    target_cloud: str = Field("gcp", description="'gcp', 'aws', or 'local'")
    simulate_healing: bool = Field(
        True,
        description="When True, intentionally triggers an initial preflight gate failure so ClosedLoopHealer executes.",
    )


class BrownfieldInspectRequest(BaseModel):
    source_mode: str = Field("sample", description="'sample' (bundled legacy repo) or 'custom'")
    target_file: str = Field("models.py", description="Relative file path for AST blast-radius calculation")
    refactor_task: str = Field(
        "Wrap AI prompt calls in GuardrailManager and externalize legacy secrets",
        max_length=300,
    )
    custom_files: dict[str, str] | None = Field(
        default=None,
        description="Optional map of relative .py file paths to source code when source_mode='custom'",
    )


class RoiRequest(BaseModel):
    team_size: int = Field(5, ge=1, le=200)
    hourly_rate: float = Field(85.0, ge=25.0, le=400.0)
    releases_per_month: int = Field(8, ge=1, le=120)
    avg_loc_per_app: int = Field(3500, ge=300, le=100000)


class GuardrailInspectRequest(BaseModel):
    payload: str = Field(..., min_length=1, max_length=2500)


class DoraTelemetry(BaseModel):
    deployment_frequency_multiplier: float
    lead_time_reduction_pct: float
    change_failure_rate_pct: float
    mttr_minutes: float


class FrameworkStatusResponse(BaseModel):
    status: str
    framework: str
    version: str
    website: str
    repository: str
    author: str
    tests_passed: int
    tests_total: int
    preflight_clearance: str
    supported_models: list[str]
    default_model: str
    mcp_enabled: bool
    stages_active: list[str]
    packages: dict[str, str]
    pricing_model: dict[str, Any]
