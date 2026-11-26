"""Nexus Orchestrator: Embedded Model Context Protocol (MCP) Server."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from typing import Any, TextIO

from nexus import __version__
from nexus.orchestrator.protocol import OrchestratorProtocol
from nexus.tools.base import Tool


class NexusMcpServer:
    """
    Embedded MCP Server for Nexus.
    Allows Claude Code, Cursor, Codex, and Gemini to interact with Nexus tools as equals.
    """

    def __init__(self, name: str = "nexus-mcp", version: str | None = None) -> None:
        self.name = name
        self.version = version if version is not None else __version__
        self.tools: dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        """Register a Nexus Tool with the MCP server."""
        self.tools[tool.name] = tool

    def handle_request(self, request_json: Mapping[str, Any]) -> dict[str, Any] | None:
        """Process an MCP JSON-RPC 2.0 request.

        Returns ``None`` for notifications (messages without an ``id``), which must
        not receive a JSON-RPC response per the MCP specification.
        """
        is_notification = "id" not in request_json
        req_id = request_json.get("id")
        method = request_json.get("method")

        if not isinstance(method, str) or not method:
            if is_notification:
                return None
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32600, "message": "Invalid Request: missing method"},
            }

        if is_notification:
            return None

        raw_params = request_json.get("params")
        if raw_params is None:
            params: Mapping[str, Any] = {}
        elif isinstance(raw_params, Mapping):
            params = raw_params
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": "Invalid params: expected an object"},
            }

        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

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
            raw_arguments = params.get("arguments")
            if raw_arguments is None:
                arguments: Mapping[str, Any] = {}
            elif isinstance(raw_arguments, Mapping):
                arguments = raw_arguments
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32602,
                        "message": "Invalid params: 'arguments' must be an object",
                    },
                }

            if not isinstance(name, str) or name not in self.tools:
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

    def run_stdio(self, stdin: TextIO | None = None, stdout: TextIO | None = None) -> None:
        """Run stdio JSON-RPC loop for Claude Code and Cursor CLI integrations."""
        in_stream = sys.stdin if stdin is None else stdin
        out_stream = sys.stdout if stdout is None else stdout

        for line in in_stream:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except Exception as exc:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {exc}"},
                }
                out_stream.write(json.dumps(err_resp) + "\n")
                out_stream.flush()
                continue

            if not isinstance(req, Mapping):
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32600, "message": "Invalid Request: expected JSON object"},
                }
                out_stream.write(json.dumps(err_resp) + "\n")
                out_stream.flush()
                continue

            resp = self.handle_request(req)
            if resp is not None:
                out_stream.write(json.dumps(resp) + "\n")
                out_stream.flush()
