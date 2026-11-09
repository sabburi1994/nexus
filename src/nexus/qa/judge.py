"""Nexus QA: LLM-as-a-judge for autonomous agent evaluation."""

from __future__ import annotations

from pydantic import BaseModel, Field

from nexus.providers.base import BaseModelProvider


class EvaluationScore(BaseModel):
    """Evaluation verdict from LLM Judge."""

    faithfulness_score: float = Field(
        ge=0.0, le=1.0, description="1.0 = zero hallucinations"
    )
    instruction_following_score: float = Field(
        ge=0.0, le=1.0, description="1.0 = followed all rules"
    )
    passed: bool = Field(description="True if both scores meet threshold")
    reasoning: str = Field(description="Detailed rationale")


class LLMJudge:
    """Evaluates agent responses against tasks and context without human labeling."""

    def __init__(self, provider: BaseModelProvider, threshold: float = 0.8) -> None:
        self.provider = provider
        self.threshold = threshold

    def evaluate(
        self, task: str, agent_output: str, reference_facts: str | None = None
    ) -> EvaluationScore:
        """Run judge evaluation."""
        prompt = f"""Evaluate the following agent response.
Task: {task}
Agent Response: {agent_output}
Reference Facts: {reference_facts or "None provided"}

Verify:
1. Did the agent follow the task instructions?
2. Did the agent remain faithful to reference facts without hallucinating?
"""
        system = "You are an impartial AI evaluation judge. Grade on a scale from 0.0 to 1.0."
        return self.provider.structured(
            prompt, EvaluationScore, system_instruction=system
        )
