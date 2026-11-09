"""Showcase Data Models using NexusEntity and Pydantic."""
from __future__ import annotations

import uuid
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
