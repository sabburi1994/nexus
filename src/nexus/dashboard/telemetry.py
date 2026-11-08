"""Nexus Dashboard: Real-time telemetry, event streaming, and agent tracking."""
from __future__ import annotations

import asyncio
import datetime
from enum import Enum
import json
from typing import Any, AsyncGenerator


class EventType(str, Enum):
    AGENT_STARTED = "agent_started"
    THOUGHT = "thought"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    COST_UPDATE = "cost_update"
    GUARDRAIL_TRIGGERED = "guardrail_triggered"
    ARTIFACT_GENERATED = "artifact_generated"
    STEP_COMPLETED = "step_completed"
    RUN_COMPLETED = "run_completed"


class AgentEvent:
    """A real-time telemetry event emitted during agent reasoning and collaboration."""

    def __init__(
        self,
        event_type: EventType | str,
        agent_name: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.event_type = event_type if isinstance(event_type, str) else event_type.value
        self.agent_name = agent_name
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "agent_name": self.agent_name,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class DashboardEventBus:
    """In-memory event bus broadcasting agent execution traces to the localhost visualizer."""

    def __init__(self) -> None:
        self._history: list[AgentEvent] = []
        self._subscribers: set[asyncio.Queue[AgentEvent]] = set()

    def emit(self, event: AgentEvent) -> None:
        """Record and broadcast an event."""
        self._history.append(event)
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return recent execution events."""
        return [e.to_dict() for e in self._history[-limit:]]

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Subscribe to real-time events for Server-Sent Events (SSE) streaming."""
        queue: asyncio.Queue[AgentEvent] = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        try:
            # Yield history first
            for event in self._history[-20:]:
                yield f"data: {event.to_json()}\n\n"

            # Stream live events
            while True:
                event = await queue.get()
                yield f"data: {event.to_json()}\n\n"
        finally:
            self._subscribers.discard(queue)


# Global singleton event bus
event_bus = DashboardEventBus()
