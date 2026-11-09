"""Nexus Orchestrator: Embedded Model Context Protocol (MCP) Server."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from typing import Any

from nexus.orchestrator.protocol import OrchestratorProtocol
from nexus.tools.base import Tool


class NexusMcpServer:
    """
    Embedded MCP Server for Nexus.
    Allows Claude Code, Cursor, Codex, and Gemini to interact with Nexus tools as equals.
    """

    def __init__(self, name: str = "nexus-mcp", version: str = "0.1.0") -> None:
        self.name = name
        self.version = version
        self.tools: dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        """Register a Nexus Tool with the MCP server."""
        self.tools[tool.name] = tool

    def handle_request(self, request_json: Mapping[str, Any]) -> dict[str, Any]:
        """Process an MCP JSON-RPC 2.0 request."""
        req_id = request_json.get("id")
        method = request_json.get("method")
        params = request_json.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": self.name, "version": self.version},
                },
            }

        if method == "tools/list":
            tool_list = [OrchestratorProtocol.to_mcp_tool(t) for t in self.tools.values()]
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": tool_list},
            }

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if name not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{name}' not found in Nexus",
                    },
                }

            tool = self.tools[name]
            try:
                res = tool.execute(**arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(res, default=str)}],
                        "isError": False,
                    },
                }
            except Exception as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error executing {name}: {exc}"}],
                        "isError": True,
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not implemented"},
        }

    def run_stdio(self) -> None:
        """Run stdio JSON-RPC loop for Claude Code and Cursor CLI integrations."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as exc:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {exc}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
