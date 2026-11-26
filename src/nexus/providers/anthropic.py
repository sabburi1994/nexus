"""Nexus Providers: Anthropic Messages API HTTP provider (Claude models)."""

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

DEFAULT_ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-5"
ANTHROPIC_API_VERSION = "2023-06-01"

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*?)\n```\s*$", re.DOTALL | re.IGNORECASE)


def _strip_json_fences(raw_text: str) -> str:
    text = raw_text.strip()
    match = _JSON_FENCE_RE.match(text)
    return match.group(1).strip() if match else text


class AnthropicProvider(BaseModelProvider):
    """Pluggable provider for Anthropic's Messages API using ``httpx`` directly."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str = DEFAULT_ANTHROPIC_MODEL,
        *,
        max_tokens: int = 8192,
        timeout_s: float = 180.0,
        max_retries: int = 3,
        http_client: httpx.Client | None = None,
    ) -> None:
        resolved_key = api_key if api_key is not None else os.getenv("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise NexusConfigurationError(
                "No Anthropic API key configured. Set ANTHROPIC_API_KEY or pass api_key explicitly."
            )
        self._api_key = resolved_key.strip()
        self.base_url = (base_url or os.getenv("ANTHROPIC_BASE_URL") or DEFAULT_ANTHROPIC_BASE_URL).rstrip("/")
        self.default_model = default_model
        self.max_tokens = max_tokens
        self.max_retries = max(1, max_retries)
        self._http = http_client or httpx.Client(timeout=httpx.Timeout(timeout_s, connect=30.0, read=timeout_s))

    @property
    def name(self) -> str:
        return "anthropic"

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
        }

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/messages"
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
                raise RuntimeError(f"anthropic request failed ({resp.status_code}): {detail}")
            data = resp.json()
            if not isinstance(data, dict):
                raise RuntimeError("anthropic returned non-object JSON payload")
            return data
        raise RuntimeError("anthropic HTTP request failed after max retries")

    @staticmethod
    def _extract_usage(data: dict[str, Any], used_model: str) -> ProviderUsage:
        usage = data.get("usage")
        if not isinstance(usage, dict):
            return ProviderUsage(0, 0, 0.0, used_model)
        inp = int(usage.get("input_tokens", 0) or 0)
        out = int(usage.get("output_tokens", 0) or 0)
        cost = calculate_cost_usd(inp, out, model=used_model)
        return ProviderUsage(inp, out, cost, used_model)

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        content = data.get("content")
        if not isinstance(content, list):
            return ""
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts)

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> ModelResponse:
        used_model = model or self.default_model
        payload: dict[str, Any] = {
            "model": used_model,
            "max_tokens": self.max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_instruction:
            payload["system"] = system_instruction

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

    def structured(
        self,
        prompt: str,
        response_model: type[T],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> T:
        self.last_usage = None
        used_model = model or self.default_model
        tool_name = "emit_structured_output"
        schema = response_model.model_json_schema()

        payload: dict[str, Any] = {
            "model": used_model,
            "max_tokens": self.max_tokens,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [
                {
                    "name": tool_name,
                    "description": f"Return structured output matching {response_model.__name__}.",
                    "input_schema": schema,
                }
            ],
            "tool_choice": {"type": "tool", "name": tool_name},
        }
        if system_instruction:
            payload["system"] = system_instruction

        data = self._post(payload)
        self.last_usage = self._extract_usage(data, used_model)

        content = data.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use" and isinstance(block.get("input"), dict):
                    return response_model.model_validate(block["input"])

        raw_text = _strip_json_fences(self._extract_text(data))
        return response_model.model_validate(json.loads(raw_text))

    def converse(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> ModelResponse:
        used_model = model or self.default_model
        payload: dict[str, Any] = {
            "model": used_model,
            "max_tokens": self.max_tokens,
            "messages": [dict(m) for m in messages],
        }
        if system_instruction:
            payload["system"] = system_instruction
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
