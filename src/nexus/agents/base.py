"""Nexus Agents: Base Autonomous Agent Primitive."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from nexus.agents.context import AgentContext
from nexus.providers.base import BaseModelProvider
from nexus.providers.vertex import VertexAIProvider
from nexus.security.guardrail import GuardrailManager
from nexus.tools.base import Tool

logger = logging.getLogger("nexus.agents")


class AgentRunResult:
    """The result of an autonomous agent task execution."""

    def __init__(
        self,
        output: str,
        turns: int,
        context: AgentContext,
    ) -> None:
        self.output = output
        self.turns = turns
        self.context = context
        self.total_cost_usd = context.accumulated_cost_usd
        self.input_tokens = context.total_input_tokens
        self.output_tokens = context.total_output_tokens

    def __repr__(self) -> str:
        return f"<AgentRunResult output={self.output[:40]!r}... turns={self.turns} cost=${self.total_cost_usd:.6f}>"


class BaseAgent:
    """
    Autonomous AI Agent Primitive.
    Handles reasoning, tool dispatching, security guardrails, and budget enforcement.
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        provider: BaseModelProvider | None = None,
        tools: Sequence[Tool] | None = None,
        guardrail: GuardrailManager | None = None,
        max_budget_usd: float = 0.50,
        max_turns: int = 6,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.provider = provider or VertexAIProvider()
        self.tools = {t.name: t for t in (tools or [])}
        self.guardrail = guardrail or GuardrailManager()
        self.max_budget_usd = max_budget_usd
        self.max_turns = max_turns

    def run(self, task: str) -> AgentRunResult:
        """Execute a task autonomously."""
        # 1. Inspect and scrub input via security guardrails
        clean_task = self.guardrail.inspect_input(task)

        # 2. Initialize execution context with spend limit
        context = AgentContext(max_budget_usd=self.max_budget_usd)
        context.add_user_message(clean_task)

        tool_schemas = [t.schema for t in self.tools.values()]
        turn_count = 0

        for turn in range(self.max_turns):
            turn_count += 1
            # Execute model turn
            resp = self.provider.converse(
                messages=context.messages,
                tools=tool_schemas,
                system_instruction=self.system_prompt,
            )
            context.record_usage(resp.input_tokens, resp.output_tokens, resp.cost_usd)

            # Check if tools were executed or final answer returned
            # If plain text returned
            if resp.text:
                context.add_model_message(resp.text)
                return AgentRunResult(output=resp.text, turns=turn_count, context=context)

        return AgentRunResult(
            output="Agent completed max turns without final message.",
            turns=turn_count,
            context=context,
        )
