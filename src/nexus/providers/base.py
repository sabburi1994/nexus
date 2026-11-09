"""Nexus Providers: Abstract interface for LLM backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ModelResponse:
    """Standardized response from any model provider."""

    def __init__(
        self,
        text: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        model: str,
        raw: Mapping[str, Any] | None = None,
    ) -> None:
        self.text = text
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cost_usd = cost_usd
        self.model = model
        self.raw = raw or {}

    def __repr__(self) -> str:
        return f"<ModelResponse model={self.model} cost=${self.cost_usd:.6f}>"


class BaseModelProvider(ABC):
    """Abstract model provider interface for Nexus Agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider (e.g. 'vertex', 'ollama', 'mock')."""
        ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> ModelResponse:
        """Single-turn generation."""
        ...

    @abstractmethod
    def structured(
        self,
        prompt: str,
        response_model: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> T:
        """Constrained structured generation adhering to a Pydantic schema."""
        ...

    @abstractmethod
    def converse(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> ModelResponse:
        """Multi-turn tool-calling turn."""
        ...
