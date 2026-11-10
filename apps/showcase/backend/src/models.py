"""Showcase Data Models using NexusEntity and Pydantic."""
from __future__ import annotations

import uuid
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy import Float, Integer, String, Text
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


# --- API Request & Response Schemas ---

class ScanRequest(BaseModel):
    target: str = Field(..., description="Entity or macro indicator to analyze")
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
    idea: str = Field(..., description="Application requirement or prompt to simulate")
    target_cloud: str = Field("gcp", description="'gcp', 'aws', or 'local'")


class AgentTraceStep(BaseModel):
    agent_name: str
    role: str
    status: str  # "completed", "running", "error"
    summary: str
    tokens: int
    cost_usd: float
    timestamp: str
    artifact_preview: str | None = None


class SimulationResponse(BaseModel):
    app_name: str
    title: str
    tagline: str
    steps: list[AgentTraceStep]
    total_tokens: int
    total_cost_usd: float
    healing_cycles: int
    verdict: str
    artifacts: dict[str, str]


class RoiRequest(BaseModel):
    team_size: int = Field(5, ge=1, le=100)
    hourly_rate: float = Field(85.0, ge=30.0, le=300.0)
    releases_per_month: int = Field(8, ge=1, le=100)
    avg_loc_per_app: int = Field(3500, ge=500, le=50000)


class DoraTelemetry(BaseModel):
    deployment_frequency_multiplier: float
    lead_time_reduction_pct: float
    change_failure_rate_pct: float
    mttr_minutes: float


class RoiResponse(BaseModel):
    team_size: int
    hourly_rate: float
    monthly_hours_saved: float
    annual_hours_saved: float
    monthly_gross_savings_usd: float
    annual_gross_savings_usd: float
    monthly_token_cost_usd: float
    annual_net_savings_usd: float
    roi_multiplier: float
    dora_metrics: DoraTelemetry
    summary: str
