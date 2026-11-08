"""Nexus Agents: Execution Context, memory, and budget tracking."""
from __future__ import annotations

import uuid
from typing import Any


class BudgetExceededError(Exception):
    """Raised when an agent session hits its spend ceiling."""
    pass


class AgentContext:
    """Manages working memory, message logs, and spend ledger for an agent run."""

    def __init__(
        self,
        session_id: str | None = None,
        max_budget_usd: float = 0.50,  # Default safety cap: $0.50 max per run
    ) -> None:
        self.session_id = session_id or str(uuid.uuid4())
        self.max_budget_usd = max_budget_usd
        self.messages: list[dict[str, Any]] = []
        self.tool_executions: list[dict[str, Any]] = []
        self.accumulated_cost_usd: float = 0.0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    def record_usage(self, input_tokens: int, output_tokens: int, cost_usd: float) -> None:
        """Record model inference tokens and check budget ceiling."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.accumulated_cost_usd += cost_usd

        if self.accumulated_cost_usd > self.max_budget_usd:
            raise BudgetExceededError(
                f"Agent session {self.session_id} exceeded max budget of ${self.max_budget_usd:.4f} "
                f"(current cost: ${self.accumulated_cost_usd:.4f})"
            )

    def add_user_message(self, text: str) -> None:
        self.messages.append({"role": "user", "parts": [{"text": text}]})

    def add_model_message(self, text: str) -> None:
        self.messages.append({"role": "model", "parts": [{"text": text}]})
