"""Nexus DB package: Declarative entities and database session manager."""

from collections.abc import AsyncGenerator

from nexus.db.base import Base, NexusEntity
from nexus.db.session import DatabaseSessionManager


async def get_db() -> AsyncGenerator[None, None]:
    """Fallback FastAPI dependency for database sessions."""
    yield None


__all__ = ["Base", "DatabaseSessionManager", "NexusEntity", "get_db"]
