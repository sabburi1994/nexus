"""Nexus Providers: Zero-Cost Mock Provider for testing and local development."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar

from pydantic import BaseModel

from nexus.providers.base import BaseModelProvider, ModelResponse

T = TypeVar("T", bound=BaseModel)


class MockProvider(BaseModelProvider):
    """Zero-cost mock provider returning predefined or dynamic responses."""

    def __init__(
        self,
        default_reply: str = "Mock agent reasoning completed.",
        structured_mock: Any = None,
    ) -> None:
        self.default_reply = default_reply
        self.structured_mock = structured_mock
        self.history: list[str] = []

    @property
    def name(self) -> str:
        return "mock"

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> ModelResponse:
        self.history.append(prompt)
        return ModelResponse(
            text=self.default_reply,
            input_tokens=len(prompt.split()),
            output_tokens=len(self.default_reply.split()),
            cost_usd=0.0,
            model="mock-agent-0.1",
        )

    def structured(
        self,
        prompt: str,
        response_model: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> T:
        self.history.append(prompt)
        if self.structured_mock:
            if isinstance(self.structured_mock, response_model):
                return self.structured_mock
            if isinstance(self.structured_mock, dict):
                return response_model.model_validate(self.structured_mock)

        # Generate a minimal valid dummy instance of the Pydantic schema
        import typing

        dummy_data: dict[str, Any] = {}
        for name, field in response_model.model_fields.items():
            origin = getattr(field.annotation, "__origin__", None)
            if field.annotation is str:
                dummy_data[name] = "mock_value"
            elif field.annotation is int:
                dummy_data[name] = 1
            elif field.annotation is float:
                dummy_data[name] = 1.0
            elif field.annotation is bool:
                dummy_data[name] = True
            elif origin is list:
                dummy_data[name] = []
            elif origin is dict:
                dummy_data[name] = {}
            elif origin is typing.Literal:
                args = getattr(field.annotation, "__args__", ())
                dummy_data[name] = args[0] if args else None
            elif isinstance(field.annotation, type) and issubclass(field.annotation, BaseModel):
                dummy_data[name] = self.structured("", field.annotation)
            else:
                dummy_data[name] = None
        return response_model.model_validate(dummy_data)

    def converse(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> ModelResponse:
        return self.generate(str(messages))
