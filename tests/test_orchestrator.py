"""Tests for Nexus Orchestrator and MCP integration."""

from __future__ import annotations

import io
import json

from nexus import __version__
from nexus.orchestrator.mcp import NexusMcpServer
from nexus.orchestrator.protocol import OrchestratorProtocol
from nexus.tools.base import Tool, ToolPermission


def test_orchestrator_protocol_formats() -> None:
    """Verify tool conversion to MCP, OpenAI, Anthropic, and Gemini schemas."""

    def sample_tool(ticker: str, limit: int = 5) -> list[str]:
        """Fetch market tickers."""
        return [ticker]

    tool = Tool(fn=sample_tool, name="get_tickers", description="Fetch market tickers")

    mcp = OrchestratorProtocol.to_mcp_tool(tool)
    assert mcp["name"] == "get_tickers"
    assert "inputSchema" in mcp

    openai = OrchestratorProtocol.to_openai_tool(tool)
    assert openai["type"] == "function"
    assert openai["function"]["name"] == "get_tickers"

    anthropic = OrchestratorProtocol.to_anthropic_tool(tool)
    assert anthropic["name"] == "get_tickers"
    assert "input_schema" in anthropic

    gemini = OrchestratorProtocol.to_gemini_tool(tool)
    assert gemini["name"] == "get_tickers"
    assert "parameters" in gemini


def test_nexus_mcp_server_initialize_and_tools() -> None:
    """Verify embedded MCP server handles initialize, tools/list, and tools/call."""
    server = NexusMcpServer(name="test-mcp", version="0.1.0")

    def ping() -> str:
        """Ping pong tool."""
        return "pong"

    server.register_tool(Tool(fn=ping, name="ping", permission=ToolPermission.READ_ONLY))

    # Initialize
    init_res = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init_res is not None
    assert init_res["result"]["serverInfo"]["name"] == "test-mcp"

    # tools/list
    list_res = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert list_res is not None
    tools = list_res["result"]["tools"]
    assert len(tools) == 1
    assert tools[0]["name"] == "ping"

    # tools/call
    call_res = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "ping", "arguments": {}},
        }
    )
    assert call_res is not None
    assert call_res["result"]["isError"] is False
    assert "pong" in call_res["result"]["content"][0]["text"]


def test_nexus_mcp_default_version_ping_and_notifications() -> None:
    """MCP server defaults to framework version, answers ping, and stays silent on notifications."""
    server = NexusMcpServer()
    assert server.version == __version__

    init_res = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init_res is not None
    assert init_res["result"]["serverInfo"]["version"] == __version__

    # Notifications (no "id") must return None per JSON-RPC 2.0 / MCP.
    assert server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert (
        server.handle_request({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 9}})
        is None
    )

    # Ping liveness check
    ping_res = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "ping"})
    assert ping_res == {"jsonrpc": "2.0", "id": 2, "result": {}}

    # Invalid params / non-mapping arguments
    bad_params = server.handle_request({"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": ["not-a-dict"]})
    assert bad_params is not None
    assert bad_params["error"]["code"] == -32602

    bad_args = server.handle_request(
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "missing", "arguments": ["bad"]}}
    )
    assert bad_args is not None
    assert bad_args["error"]["code"] == -32602


def test_nexus_mcp_stdio_skips_notifications_and_handles_bad_frames() -> None:
    """run_stdio emits no frame for notifications and returns JSON-RPC errors on bad input."""
    server = NexusMcpServer()
    inbound = io.StringIO(
        "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping"}),
                "not-json",
                "[1, 2, 3]",
            ]
        )
        + "\n"
    )
    outbound = io.StringIO()
    server.run_stdio(stdin=inbound, stdout=outbound)

    lines = [json.loads(line) for line in outbound.getvalue().splitlines() if line.strip()]
    assert len(lines) == 4  # initialize, ping, parse error, invalid request (no frame for notification)
    assert lines[0]["id"] == 1
    assert lines[0]["result"]["serverInfo"]["version"] == __version__
    assert lines[1] == {"jsonrpc": "2.0", "id": 2, "result": {}}
    assert lines[2]["error"]["code"] == -32700
    assert lines[3]["error"]["code"] == -32600
