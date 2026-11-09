"""Token pricing and spend tracking for Vertex AI models."""

from __future__ import annotations

from typing import Final

# Vertex AI Gemini 3.8 Flash pricing per million tokens
GEMINI_3_8_FLASH_INPUT_PER_M: Final[float] = 0.075
GEMINI_3_8_FLASH_OUTPUT_PER_M: Final[float] = 0.30

# Fallback default model
DEFAULT_MODEL: Final[str] = "gemini-3.8-flash"


def calculate_cost_usd(
    input_tokens: int,
    output_tokens: int,
    model: str = DEFAULT_MODEL,
) -> float:
    """Calculate the estimated USD cost for a model call."""
    if "gemini-3.8" in model or "gemini-3" in model:
        in_cost = (input_tokens / 1_000_000.0) * GEMINI_3_8_FLASH_INPUT_PER_M
        out_cost = (output_tokens / 1_000_000.0) * GEMINI_3_8_FLASH_OUTPUT_PER_M
        return in_cost + out_cost
    # Standard Gemini 2.x / 1.5 pricing baseline
    in_cost = (input_tokens / 1_000_000.0) * 0.15
    out_cost = (output_tokens / 1_000_000.0) * 0.60
    return in_cost + out_cost
