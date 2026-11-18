"""Nexus DB: Declarative Base and standard entity mixins."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all Nexus database models."""


class NexusEntity(Base):
    """Abstract base model with UUID primary key and timestamp tracking."""

    __abstract__ = True

    # Generic Uuid: native UUID on PostgreSQL, CHAR(32) on SQLite (generated apps default to SQLite).
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
