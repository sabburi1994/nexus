"""Nexus Security: Pre and post-execution guardrail manager."""

from __future__ import annotations

from typing import Any

from nexus.security.injection import check_prompt_injection
from nexus.security.sanitizer import sanitize_text
from nexus.tools.base import Tool, ToolPermission


class SecurityViolationError(Exception):
    """Raised when a security guardrail detects malicious activity."""


class GuardrailManager:
    """Enforces safety guardrails across inputs, agent reasoning, and tool execution."""

    def __init__(
        self,
        block_injections: bool = True,
        sanitize_inputs: bool = True,
        require_approval_for_critical_tools: bool = True,
    ) -> None:
        self.block_injections = block_injections
        self.sanitize_inputs = sanitize_inputs
        self.require_approval = require_approval_for_critical_tools

    def inspect_input(self, prompt: str) -> str:
        """Validate and scrub input before model execution."""
        if self.block_injections:
            check = check_prompt_injection(prompt)
            if not check.is_safe:
                raise SecurityViolationError(
                    f"Prompt blocked by Nexus Injection Guardrail: '{check.matched_pattern}'"
                )

        if self.sanitize_inputs:
            return sanitize_text(prompt)

        return prompt

    def authorize_tool_execution(self, tool: Tool, args: dict[str, Any]) -> None:
        """Verify tool execution privileges."""
        if tool.permission == ToolPermission.CRITICAL and self.require_approval:
            # Critical tools require affirmative authorization
            raise SecurityViolationError(
                f"Execution of CRITICAL tool '{tool.name}' requires explicit authorization."
            )
