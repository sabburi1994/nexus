"""Nexus Orchestrator: Universal Protocol Translators (MCP, Claude, OpenAI, Gemini)."""

from __future__ import annotations

from typing import Any

from nexus.tools.base import Tool


class OrchestratorProtocol:
    """Translates Nexus agents and tools into standard formats for Claude Code, Cursor, Codex, and Gemini."""

    @staticmethod
    def to_mcp_tool(tool: Tool) -> dict[str, Any]:
        """Convert Nexus Tool to Model Context Protocol (MCP) tool format."""
        schema = tool.schema
        return {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": schema.get(
                "parameters", {"type": "object", "properties": {}}
            ),
        }

    @staticmethod
    def to_openai_tool(tool: Tool) -> dict[str, Any]:
        """Convert Nexus Tool to OpenAI function format."""
        schema = tool.schema
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": schema.get(
                    "parameters", {"type": "object", "properties": {}}
                ),
            },
        }

    @staticmethod
    def to_anthropic_tool(tool: Tool) -> dict[str, Any]:
        """Convert Nexus Tool to Anthropic Claude Code format."""
        schema = tool.schema
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": schema.get(
                "parameters", {"type": "object", "properties": {}}
            ),
        }

    @staticmethod
    def to_gemini_tool(tool: Tool) -> dict[str, Any]:
        """Convert Nexus Tool to Google Gemini function declaration format."""
        schema = tool.schema
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": schema.get(
                "parameters", {"type": "object", "properties": {}}
            ),
        }
