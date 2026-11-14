"""Nexus Providers: spend cap wrapper that records every call against an AgentContext."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

from nexus.providers.base import BaseModelProvider, ModelResponse

if TYPE_CHECKING:
    from nexus.agents.context import AgentContext

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger("nexus.providers.budget")


class BudgetedProvider(BaseModelProvider):
    """Wraps a provider and records the usage of each call in ``context``.

    ``AgentContext.record_usage`` raises ``BudgetExceededError`` as soon as the accumulated
    cost passes ``context.max_budget_usd``, which stops the run before the next call. The
    call that crosses the cap has already been paid for, so the overshoot is at most one call.

    ``structured`` calls are counted through the inner provider's ``last_usage``. Providers
    that do not set it are counted as $0 (a warning is logged once).
    """

    def __init__(self, inner: BaseModelProvider, context: AgentContext) -> None:
        self.inner = inner
        self.context = context
        self._warned_unreported = False

    @property
    def name(self) -> str:
        return self.inner.name

    def __getattr__(self, item: str) -> Any:
        # Provider specific attributes (call logs, clients) stay reachable through the wrapper.
        if item == "inner":
            raise AttributeError(item)
        return getattr(self.inner, item)

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> ModelResponse:
        resp = self.inner.generate(prompt, system_instruction=system_instruction, model=model, temperature=temperature)
        self.context.record_usage(resp.input_tokens, resp.output_tokens, resp.cost_usd)
        return resp

    def structured(
        self,
        prompt: str,
        response_model: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> T:
        self.last_usage = None
        self.inner.last_usage = None
        result = self.inner.structured(prompt, response_model, system_instruction=system_instruction, model=model)
        usage = self.inner.last_usage
        if usage is None:
            if not self._warned_unreported:
                logger.warning(
                    "Provider %r does not report structured() usage; its calls count as $0 against the budget.",
                    self.inner.name,
                )
                self._warned_unreported = True
            return result
        self.last_usage = usage
        self.context.record_usage(usage.input_tokens, usage.output_tokens, usage.cost_usd)
        return result

    def converse(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> ModelResponse:
        resp = self.inner.converse(messages, tools, system_instruction=system_instruction, model=model)
        self.context.record_usage(resp.input_tokens, resp.output_tokens, resp.cost_usd)
        return resp
