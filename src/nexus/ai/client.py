"""Nexus AI: Standardized Google Cloud Vertex AI & Gemini 3.8 Client."""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from typing import Any, Callable, Mapping, Sequence, TypeVar
import httpx
from pydantic import BaseModel

from nexus.ai.pricing import DEFAULT_MODEL, calculate_cost_usd

logger = logging.getLogger("nexus.ai")

# Cache token locally for 40 minutes to prevent overhead
_CACHED_TOKEN: tuple[str, float] | None = None
_TOKEN_TTL_SECONDS = 40 * 60

T = TypeVar("T", bound=BaseModel)


def get_gcp_project() -> str:
    """Resolve the active Google Cloud project ID."""
    proj = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if proj:
        return proj
    gcloud_bin = shutil.which("gcloud") or shutil.which("gcloud.cmd")
    if gcloud_bin:
        try:
            res = subprocess.run(
                [gcloud_bin, "config", "get-value", "project"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            val = res.stdout.strip()
            if val and val != "(unset)":
                return val
        except Exception:
            pass
    return "finhub-510316"


def get_gcp_access_token() -> str | None:
    """Acquire an OAuth access token via IAM instance metadata or gcloud CLI."""
    global _CACHED_TOKEN
    now = time.time()
    if _CACHED_TOKEN and (now - _CACHED_TOKEN[1]) < _TOKEN_TTL_SECONDS:
        return _CACHED_TOKEN[0]

    # 1. Environment token override
    env_token = os.getenv("GCP_ACCESS_TOKEN") or os.getenv("GOOGLE_OAUTH_ACCESS_TOKEN")
    if env_token:
        _CACHED_TOKEN = (env_token.strip(), now)
        return env_token.strip()

    # 2. Check GCP Compute Engine / Cloud Run instance metadata server
    try:
        resp = httpx.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"},
            timeout=1.5,
        )
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            if token:
                _CACHED_TOKEN = (token, now)
                return str(token)
    except Exception:
        pass

    # 3. Local development fallback: gcloud auth print-access-token
    gcloud_bin = shutil.which("gcloud") or shutil.which("gcloud.cmd")
    if gcloud_bin:
        try:
            res = subprocess.run(
                [gcloud_bin, "auth", "print-access-token"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            token = res.stdout.strip()
            if token and res.returncode == 0 and not token.startswith("ERROR"):
                _CACHED_TOKEN = (token, now)
                return token
        except Exception as exc:
            logger.debug("Local gcloud token lookup failed: %s", exc)

    return None


class GeminiResponse:
    """Normalized response from Gemini 3.8."""

    def __init__(
        self,
        text: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        model: str,
        raw: Mapping[str, Any],
    ) -> None:
        self.text = text
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cost_usd = cost_usd
        self.model = model
        self.raw = raw

    def __repr__(self) -> str:
        return f"<GeminiResponse model={self.model} cost=${self.cost_usd:.6f} length={len(self.text)}>"


class GeminiClient:
    """
    Standardized client for Google Cloud Vertex AI & Gemini 3.8 Flash.
    Provides structured schema extraction, multimodal parsing, and multi-turn tool loops.
    """

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "global",
        api_key: str | None = None,
        default_model: str = DEFAULT_MODEL,
    ) -> None:
        self.project_id = project_id or get_gcp_project()
        self.location = location
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.default_model = default_model
        self._http = httpx.Client(timeout=httpx.Timeout(180.0, connect=30.0, read=180.0))

    def _post(self, url: str, headers: dict[str, str], body: dict[str, Any], max_retries: int = 2) -> httpx.Response:
        import time
        for attempt in range(max_retries):
            try:
                return self._http.post(url, headers=headers, json=body)
            except (httpx.ReadTimeout, httpx.ConnectTimeout):
                if attempt == max_retries - 1:
                    raise
                time.sleep(2.0)

    def _build_url_and_headers(self, model: str) -> tuple[str, dict[str, str]]:
        token = get_gcp_access_token()
        if token:
            # Vertex AI global or regional publisher endpoint
            if self.location == "global":
                url = (
                    f"https://aiplatform.googleapis.com/v1/projects/{self.project_id}"
                    f"/locations/global/publishers/google/models/{model}:generateContent"
                )
            else:
                url = (
                    f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}"
                    f"/locations/{self.location}/publishers/google/models/{model}:generateContent"
                )
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            return url, headers

        if self.api_key:
            # Direct Google Generative Language API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            return url, headers

        raise RuntimeError(
            "No Google Cloud authentication found. Provide GCP IAM credentials, run "
            "'gcloud auth application-default login', or set GEMINI_API_KEY."
        )

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> GeminiResponse:
        """Execute a text completion turn."""
        chosen_model = model or self.default_model
        url, headers = self._build_url_and_headers(chosen_model)

        body: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "thinkingConfig": {"thinkingLevel": "low"},
            },
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        resp = self._post(url, headers=headers, body=body)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API returned status {resp.status_code}: {resp.text}")

        data = resp.json()
        usage = data.get("usageMetadata", {})
        inp = int(usage.get("promptTokenCount", 0))
        out = int(usage.get("candidatesTokenCount", 0))
        cost = calculate_cost_usd(inp, out, chosen_model)

        candidates = data.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for p in parts:
                if "text" in p:
                    text += p["text"]

        return GeminiResponse(
            text=text.strip(),
            input_tokens=inp,
            output_tokens=out,
            cost_usd=cost,
            model=chosen_model,
            raw=data,
        )

    def structured(
        self,
        prompt: str,
        response_model: type[T],
        system_instruction: str | None = None,
        inline_pdf_bytes: bytes | None = None,
        model: str | None = None,
    ) -> T:
        """Extract a strongly typed Pydantic schema using constrained JSON generation."""
        chosen_model = model or self.default_model
        url, headers = self._build_url_and_headers(chosen_model)

        parts: list[dict[str, Any]] = []
        if inline_pdf_bytes:
            import base64
            b64 = base64.b64encode(inline_pdf_bytes).decode("ascii")
            parts.append({"inlineData": {"mimeType": "application/pdf", "data": b64}})
        parts.append({"text": prompt})

        # Generate JSON Schema from Pydantic model
        schema = response_model.model_json_schema()
        # Clean $defs / titles if needed for Gemini schema compatibility
        clean_schema = self._sanitize_schema(schema)

        body: dict[str, Any] = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
                "responseSchema": clean_schema,
                "thinkingConfig": {"thinkingLevel": "low"},
            },
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        resp = self._post(url, headers=headers, body=body)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini structured output failed {resp.status_code}: {resp.text}")

        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"No candidates returned in structured output: {data}")

        parts_out = candidates[0].get("content", {}).get("parts", [])
        raw_text = "".join(p.get("text", "") for p in parts_out).strip()
        parsed_json = json.loads(raw_text)
        return response_model.model_validate(parsed_json)

    def converse(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[Callable[..., Any]] | Sequence[dict[str, Any]],
        system_instruction: str | None = None,
        max_turns: int = 5,
        model: str | None = None,
    ) -> GeminiResponse:
        """Multi-turn tool-calling loop executing tools locally without hallucinations."""
        chosen_model = model or self.default_model
        url, headers = self._build_url_and_headers(chosen_model)

        # Convert tools to function declarations
        func_declarations: list[dict[str, Any]] = []
        tool_dispatch: dict[str, Callable[..., Any]] = {}
        for t in tools:
            if callable(t):
                fn_name = getattr(t, "__name__", "tool")
                doc = getattr(t, "__doc__", "") or f"Execute {fn_name}"
                tool_dispatch[fn_name] = t
                func_declarations.append({
                    "name": fn_name,
                    "description": doc.strip(),
                    "parameters": {"type": "object", "properties": {}},
                })
            elif isinstance(t, dict):
                func_declarations.append(t)

        current_contents = list(messages)
        total_inp = 0
        total_out = 0

        for _ in range(max_turns):
            body: dict[str, Any] = {
                "contents": current_contents,
                "generationConfig": {
                    "temperature": 0.1,
                    "thinkingConfig": {"thinkingLevel": "low"},
                },
            }
            if func_declarations:
                body["tools"] = [{"functionDeclarations": func_declarations}]
            if system_instruction:
                body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            resp = self._post(url, headers=headers, body=body)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini converse error {resp.status_code}: {resp.text}")

            data = resp.json()
            usage = data.get("usageMetadata", {})
            total_inp += int(usage.get("promptTokenCount", 0))
            total_out += int(usage.get("candidatesTokenCount", 0))

            candidate = (data.get("candidates") or [{}])[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            # Check if model requested tool call
            function_calls = [p["functionCall"] for p in parts if "functionCall" in p]
            if not function_calls:
                # Text answer completed
                text = "".join(p.get("text", "") for p in parts).strip()
                cost = calculate_cost_usd(total_inp, total_out, chosen_model)
                return GeminiResponse(text, total_inp, total_out, cost, chosen_model, data)

            # Append model turn to conversation
            current_contents.append({"role": "model", "parts": parts})

            # Execute tool and append functionResponse
            response_parts = []
            for call in function_calls:
                name = call.get("name", "")
                args = call.get("args", {})
                fn = tool_dispatch.get(name)
                try:
                    result = fn(**args) if fn else {"status": "error", "message": f"Tool {name} not found"}
                except Exception as exc:
                    result = {"status": "error", "message": str(exc)}

                response_parts.append({
                    "functionResponse": {
                        "name": name,
                        "response": {"output": result if isinstance(result, (dict, list)) else str(result)},
                    }
                })
            current_contents.append({"role": "user", "parts": response_parts})

        raise RuntimeError(f"Gemini converse exceeded max_turns={max_turns}")

    @staticmethod
    def _sanitize_schema(schema: dict[str, Any]) -> dict[str, Any]:
        """Strip keywords unsupported by Gemini JSON Schema parser."""
        s = json.loads(json.dumps(schema))
        for key in ("title", "$defs", "$schema", "default"):
            s.pop(key, None)
        return s
