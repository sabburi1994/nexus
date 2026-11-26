"""NexusEntity works on SQLite, the default database of generated apps (found by the real model benchmark)."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Uuid, create_engine
from sqlalchemy.orm import Mapped, Session, mapped_column

from nexus.db import Base, NexusEntity


class Org(NexusEntity):
    __tablename__ = "bench_orgs"
    name: Mapped[str] = mapped_column(String(80))


class Member(NexusEntity):
    __tablename__ = "bench_members"
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bench_orgs.id"))
    name: Mapped[str] = mapped_column(String(80))


def test_uuid_ids_and_foreign_keys_round_trip_on_sqlite() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine, tables=[Org.__table__, Member.__table__])  # type: ignore[list-item]
    with Session(engine) as db:
        org = Org(name="Apex")
        db.add(org)
        db.commit()
        db.add_all([Member(org_id=org.id, name="a"), Member(org_id=org.id, name="b")])
        db.commit()
        assert isinstance(org.id, uuid.UUID)
        members = db.query(Member).filter_by(org_id=org.id).all()
        assert {m.name for m in members} == {"a", "b"}
        assert all(m.created_at is not None for m in members)
    engine.dispose()
