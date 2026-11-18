"""Token pricing and spend tracking for Vertex AI models.

Prices are USD per million tokens on the Vertex AI global endpoint (regional endpoints cost about
10 % more), standard pay as you go. Google publishes dated price changes; the table keeps each
model's prices with the date they take effect, so a cap computed in January 2027 uses January's
price. Thinking tokens are billed as output. Check https://cloud.google.com/vertex-ai/pricing when
adding a model.
"""

from __future__ import annotations

import datetime
from typing import Final

# Fallback default model
DEFAULT_MODEL: Final[str] = "gemini-3.8-flash"

# model -> [(effective from, input per million, output per million)], oldest first.
MODEL_PRICES: Final[dict[str, list[tuple[datetime.date, float, float]]]] = {
    # Introductory price until 2026-12-31, standard price from 2027-01-01.
    "gemini-3.8-flash": [
        (datetime.date(2000, 1, 1), 0.75, 3.75),
        (datetime.date(2027, 1, 1), 1.50, 7.50),
    ],
}

# Unknown models are priced like the most expensive known Flash price, so a spend cap never
# undercounts them; add the model to MODEL_PRICES for an exact figure.
FALLBACK_PRICE: Final[tuple[float, float]] = (1.50, 7.50)


def price_per_million(model: str = DEFAULT_MODEL, on: datetime.date | None = None) -> tuple[float, float]:
    """(input, output) USD per million tokens for ``model`` on ``on`` (default: today, UTC)."""
    day = on or datetime.datetime.now(datetime.UTC).date()
    name = model.removeprefix("models/").split("@")[0]
    schedule = MODEL_PRICES.get(name)
    if not schedule:
        return FALLBACK_PRICE
    current = schedule[0]
    for entry in schedule:
        if entry[0] <= day:
            current = entry
    return current[1], current[2]


# Kept for callers of earlier versions: today's gemini-3.8-flash price when this module is imported.
GEMINI_3_8_FLASH_INPUT_PER_M, GEMINI_3_8_FLASH_OUTPUT_PER_M = price_per_million("gemini-3.8-flash")


def calculate_cost_usd(
    input_tokens: int,
    output_tokens: int,
    model: str = DEFAULT_MODEL,
    on: datetime.date | None = None,
) -> float:
    """Calculate the estimated USD cost for a model call (output tokens include thinking tokens)."""
    price_in, price_out = price_per_million(model, on)
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000.0
