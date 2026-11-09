"""Quickstart Example: Creating an autonomous agent with Nexus and Gemini 3.8 Flash."""
from __future__ import annotations

import os
from nexus.ai.client import GeminiClient
from nexus.agents.base import BaseAgent, AgentContext
from nexus.tools import tool, ToolPermission


# 1. Define custom tools with permissions
@tool(permission=ToolPermission.READ_ONLY, description="Lookup current market price for an asset.")
def get_asset_price(ticker: str) -> dict:
    return {"ticker": ticker.upper(), "price_eur": 420.50, "trend": "bullish"}


def main() -> None:
    # 2. Instantiate Vertex AI provider for Gemini 3.8 Flash
    from nexus.providers.vertex import VertexAIProvider

    provider = VertexAIProvider(default_model="gemini-3.8-flash")

    # 3. Create autonomous agent with micro-budget ceiling
    agent = BaseAgent(
        name="MarketAnalyst",
        system_prompt="You are a financial researcher. Use available tools to analyze assets and give brief investment takeaways.",
        provider=provider,
        tools=[get_asset_price],
        max_budget_usd=0.01,  # Strict budget ceiling
    )

    # 4. Execute prompt
    print("--- Executing Nexus Quickstart Agent ---")
    result = agent.run("What is the current status of BTC?")
    print("\nAgent Response:\n", result.output)
    print(f"\nExecution Spend: ${result.total_cost_usd:.6f} USD (Turns: {result.turns})")


if __name__ == "__main__":
    main()
