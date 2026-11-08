"""Nexus Providers: Google Cloud Vertex AI & Gemini 3.8 Flash Provider."""
from __future__ import annotations

from typing import Any, Sequence, TypeVar
from pydantic import BaseModel

from nexus.ai.client import GeminiClient
from nexus.providers.base import BaseModelProvider, ModelResponse

T = TypeVar("T", bound=BaseModel)


class VertexAIProvider(BaseModelProvider):
    """Google Cloud Vertex AI provider optimized for Gemini 3.8 Flash."""

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "global",
        default_model: str = "gemini-3.8-flash",
    ) -> None:
        self._client = GeminiClient(
            project_id=project_id,
            location=location,
            default_model=default_model,
        )

    @property
    def name(self) -> str:
        return "vertex"

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> ModelResponse:
        res = self._client.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            model=model,
            temperature=temperature,
        )
        return ModelResponse(
            text=res.text,
            input_tokens=res.input_tokens,
            output_tokens=res.output_tokens,
            cost_usd=res.cost_usd,
            model=res.model,
            raw=res.raw,
        )

    def structured(
        self,
        prompt: str,
        response_model: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> T:
        return self._client.structured(
            prompt=prompt,
            response_model=response_model,
            system_instruction=system_instruction,
            model=model,
        )

    def converse(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> ModelResponse:
        res = self._client.converse(
            messages=messages,
            tools=tools,
            system_instruction=system_instruction,
            model=model,
        )
        return ModelResponse(
            text=res.text,
            input_tokens=res.input_tokens,
            output_tokens=res.output_tokens,
            cost_usd=res.cost_usd,
            model=res.model,
            raw=res.raw,
        )
