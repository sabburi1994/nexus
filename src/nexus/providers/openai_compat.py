"""Nexus Providers: OpenAI-compatible HTTP provider (OpenAI, Ollama, vLLM, OpenRouter, LM Studio)."""

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Sequence
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from nexus.ai.client import NexusConfigurationError
from nexus.ai.pricing import calculate_cost_usd
from nexus.providers.base import BaseModelProvider, ModelResponse, ProviderUsage
from nexus.security import sanitize_text

T = TypeVar("T", bound=BaseModel)

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_OLLAMA_MODEL = "llama3.1"

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*?)\n```\s*$", re.DOTALL | re.IGNORECASE)


def _strip_json_fences(raw_text: str) -> str:
    text = raw_text.strip()
    match = _JSON_FENCE_RE.match(text)
    return match.group(1).strip() if match else text


class OpenAICompatibleProvider(BaseModelProvider):
    """Pluggable provider for any OpenAI Chat Completions compatible endpoint.

    Supports OpenAI cloud (``OPENAI_API_KEY``), local runtimes such as Ollama or vLLM
    (via ``base_url`` and ``zero_cost=True``), and hosted OpenAI-compatible gateways.
    Uses ``httpx`` directly with no additional SDK dependencies.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str = DEFAULT_OPENAI_MODEL,
        *,
        provider_name: str = "openai",
        zero_cost: bool = False,
        timeout_s: float = 180.0,
        max_retries: int = 3,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._provider_name = provider_name
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE_URL).rstrip("/")
        self.default_model = default_model
        self.zero_cost = zero_cost
        self.max_retries = max(1, max_retries)
        resolved_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        if not resolved_key and not zero_cost:
            raise NexusConfigurationError(
                "No OpenAI API key configured. Set OPENAI_API_KEY or pass api_key explicitly."
            )
        self._api_key = (resolved_key or "").strip()
        self._http = http_client or httpx.Client(timeout=httpx.Timeout(timeout_s, connect=30.0, read=timeout_s))

    @property
    def name(self) -> str:
        return self._provider_name

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = self._headers()
        attempt = 0
        while attempt < self.max_retries:
            try:
                resp = self._http.post(url, headers=headers, json=payload)
            except httpx.TransportError:
                attempt += 1
                if attempt == self.max_retries:
                    raise
                time.sleep(2.0 * attempt)
                continue
            if resp.status_code >= 400:
                detail = sanitize_text(resp.text[:400])
                raise RuntimeError(f"{self._provider_name} request failed ({resp.status_code}): {detail}")
            data = resp.json()
            if not isinstance(data, dict):
                raise RuntimeError(f"{self._provider_name} returned non-object JSON payload")
            return data
        raise RuntimeError(f"{self._provider_name} HTTP request failed after max retries")

    def _extract_usage(self, data: dict[str, Any], used_model: str) -> ProviderUsage:
        usage = data.get("usage")
        if not isinstance(usage, dict):
            return ProviderUsage(0, 0, 0.0, used_model)
        inp = int(usage.get("prompt_tokens", 0) or 0)
        out = int(usage.get("completion_tokens", 0) or 0)
        cost = 0.0 if self.zero_cost else calculate_cost_usd(inp, out, model=used_model)
        return ProviderUsage(inp, out, cost, used_model)

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0]
        if not isinstance(first, dict):
            return ""
        msg = first.get("message")
        if not isinstance(msg, dict):
            return ""
        content = msg.get("content")
        return content if isinstance(content, str) else ""

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> ModelResponse:
        used_model = model or self.default_model
        messages: list[dict[str, Any]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        data = self._post({"model": used_model, "messages": messages, "temperature": temperature})
        usage = self._extract_usage(data, used_model)
        return ModelResponse(
            text=self._extract_text(data),
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cost_usd=usage.cost_usd,
            model=used_model,
            raw=data,
        )

    def structured(
        self,
        prompt: str,
        response_model: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> T:
        self.last_usage = None
        used_model = model or self.default_model
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        schema_directive = (
            "Respond with a single valid JSON object matching this JSON Schema. "
            f"Do not include markdown fences or prose.\n\nSchema:\n{schema_json}"
        )
        full_system = f"{system_instruction}\n\n{schema_directive}" if system_instruction else schema_directive
        payload: dict[str, Any] = {
            "model": used_model,
            "messages": [
                {"role": "system", "content": full_system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }
        data = self._post(payload)
        self.last_usage = self._extract_usage(data, used_model)
        raw_text = _strip_json_fences(self._extract_text(data))
        return response_model.model_validate_json(raw_text)

    def converse(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> ModelResponse:
        used_model = model or self.default_model
        outbound_messages: list[dict[str, Any]] = []
        if system_instruction:
            outbound_messages.append({"role": "system", "content": system_instruction})
        outbound_messages.extend(dict(m) for m in messages)

        payload: dict[str, Any] = {
            "model": used_model,
            "messages": outbound_messages,
        }
        if tools:
            payload["tools"] = [dict(t) for t in tools]

        data = self._post(payload)
        usage = self._extract_usage(data, used_model)
        return ModelResponse(
            text=self._extract_text(data),
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cost_usd=usage.cost_usd,
            model=used_model,
            raw=data,
        )
