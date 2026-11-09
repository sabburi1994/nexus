"""Nexus Maintenance: Autonomous error diagnosis and self-healing agent."""

from __future__ import annotations

from pydantic import BaseModel, Field

from nexus.providers.base import BaseModelProvider


class DiagnosisResult(BaseModel):
    """Structured diagnosis and remediation from the self-healing agent."""

    root_cause: str = Field(description="Underlying cause of the exception or failure")
    suggested_fix: str = Field(description="Step-by-step resolution or code diff")
    is_transient: bool = Field(description="True if error was network/rate-limit related")
    confidence: float = Field(ge=0.0, le=1.0)


class AutonomousHealer:
    """Diagnoses runtime exceptions and generates automated fixes."""

    def __init__(self, provider: BaseModelProvider) -> None:
        self.provider = provider

    def diagnose_failure(
        self, error_message: str, stack_trace: str, context_snippet: str | None = None
    ) -> DiagnosisResult:
        """Diagnose a failure autonomously."""
        prompt = f"""Diagnose the following application failure:
Error: {error_message}
Stack Trace:
{stack_trace}

Context Code:
{context_snippet or "No snippet provided"}
"""
        system = "You are an autonomous site-reliability engineer and codebase maintainer."
        return self.provider.structured(prompt, DiagnosisResult, system_instruction=system)
