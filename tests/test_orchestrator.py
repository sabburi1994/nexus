"""Tests for Nexus Orchestrator and MCP integration."""

from __future__ import annotations

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
    assert init_res["result"]["serverInfo"]["name"] == "test-mcp"

    # tools/list
    list_res = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
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
    assert call_res["result"]["isError"] is False
    assert "pong" in call_res["result"]["content"][0]["text"]
