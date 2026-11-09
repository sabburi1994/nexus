"""Nexus Tools: Strongly-typed, permission-governed tool definitions for agents."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import create_model


class ToolPermission(str, Enum):
    """Permission level governing when and how an agent can execute a tool."""

    READ_ONLY = "read_only"  # Safe, read-only operations (e.g. search, queries)
    MUTATION = "mutation"  # State changes (e.g. database updates, sending email)
    CRITICAL = "critical"  # High-risk actions (e.g. live trading, deleting records)


class Tool:
    """A strongly-typed, executable capability exposed to an autonomous agent."""

    def __init__(
        self,
        fn: Callable[..., Any],
        name: str | None = None,
        description: str | None = None,
        permission: ToolPermission = ToolPermission.READ_ONLY,
    ) -> None:
        self.fn = fn
        self.name = name or fn.__name__
        self.description = (description or fn.__doc__ or f"Execute {self.name}").strip()
        self.permission = permission
        self.schema = self._generate_schema()

    def _generate_schema(self) -> dict[str, Any]:
        """Auto-generate JSON Schema parameters from Python type hints."""
        sig = inspect.signature(self.fn)
        fields: dict[str, Any] = {}
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue
            annotation = (
                param.annotation if param.annotation != inspect.Parameter.empty else Any
            )
            default = param.default if param.default != inspect.Parameter.empty else ...
            fields[param_name] = (annotation, default)

        pydantic_model = create_model(f"{self.name}_Args", **fields)
        json_schema = pydantic_model.model_json_schema()
        # Clean extra fields for model tool compatibility
        properties = json_schema.get("properties", {})
        required = json_schema.get("required", [])

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def execute(self, **kwargs: Any) -> Any:
        """Execute the underlying function."""
        return self.fn(**kwargs)

    def __call__(self, **kwargs: Any) -> Any:
        return self.execute(**kwargs)


def tool(
    name: str | None = None,
    description: str | None = None,
    permission: ToolPermission = ToolPermission.READ_ONLY,
) -> Callable[[Callable[..., Any]], Tool]:
    """Decorator to declare an agent tool."""

    def decorator(fn: Callable[..., Any]) -> Tool:
        return Tool(fn=fn, name=name, description=description, permission=permission)

    return decorator
