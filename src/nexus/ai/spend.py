"""Nexus AI: persistent monthly AI spend ledger and a monthly budget gate.

Per run caps (``AgentContext``, ``BudgetedProvider``) stop one squad run; apps also need one cap per
calendar month across every request and every instance. This module provides:

* ``SpendLedger``: the interface (record a billed call, sum a month);
* ``InMemorySpendLedger``: for tests and local development;
* ``SqlSpendLedger``: SQLAlchemy Core table ``nexus_ai_spend``, works with a sync ``Engine`` or an
  ``AsyncEngine`` (the app's existing database);
* ``MonthlyBudget``: ``await budget.ensure_within_budget()`` before every billed call,
  ``await budget.record(...)`` after it, ``await budget.summary()`` for a status readout.

Months are UTC calendar months (``YYYY-MM``). A cap of 0 or less means unlimited.
"""

from __future__ import annotations

import abc
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, DateTime, Float, Integer, MetaData, String, Table, func, insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

from nexus.agents.context import BudgetExceededError

logger = logging.getLogger("nexus.ai.spend")


def month_of(moment: datetime) -> str:
    """UTC calendar month of ``moment`` as ``YYYY-MM``."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC).strftime("%Y-%m")


@dataclass(frozen=True)
class SpendEntry:
    usd: float
    model: str
    task: str
    subject: str | None
    at: datetime


class SpendLedger(abc.ABC):
    """Durable record of billed model calls."""

    @abc.abstractmethod
    async def record(self, entry: SpendEntry) -> None:
        """Append one billed call."""

    @abc.abstractmethod
    async def month_total(self, month: str) -> float:
        """Sum of ``usd`` for the month (``YYYY-MM``)."""


class InMemorySpendLedger(SpendLedger):
    """Process local ledger (tests, local development)."""

    def __init__(self) -> None:
        self.entries: list[SpendEntry] = []

    async def record(self, entry: SpendEntry) -> None:
        self.entries.append(entry)

    async def month_total(self, month: str) -> float:
        return float(sum(e.usd for e in self.entries if month_of(e.at) == month))


def spend_table(metadata: MetaData, name: str = "nexus_ai_spend") -> Table:
    """The ledger table, for an app's own ``MetaData`` (and Alembic autogenerate)."""
    return Table(
        name,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("month", String(7), nullable=False, index=True),
        Column("at", DateTime(timezone=True), nullable=False),
        Column("usd", Float, nullable=False),
        Column("model", String(120), nullable=False),
        Column("task", String(120), nullable=False),
        Column("subject", String(200), nullable=True),
    )


class SqlSpendLedger(SpendLedger):
    """Ledger in a SQL table. Pass the app's engine (sync or async) and optionally its table.

    With a sync ``Engine`` the queries run in a worker thread, so the event loop is never blocked.
    Call ``create_table()`` once (or include ``spend_table(metadata)`` in the app's migrations).
    """

    def __init__(self, engine: Engine | AsyncEngine, table: Table | None = None) -> None:
        self.engine = engine
        self.table = table if table is not None else spend_table(MetaData())

    async def create_table(self) -> None:
        if isinstance(self.engine, AsyncEngine):
            async with self.engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: self.table.create(sync_conn, checkfirst=True))
        else:
            from anyio import to_thread

            engine = self.engine
            await to_thread.run_sync(lambda: self.table.create(engine, checkfirst=True))

    async def record(self, entry: SpendEntry) -> None:
        stmt = insert(self.table).values(
            month=month_of(entry.at),
            at=entry.at,
            usd=float(entry.usd),
            model=entry.model[:120],
            task=entry.task[:120],
            subject=entry.subject[:200] if entry.subject else None,
        )
        if isinstance(self.engine, AsyncEngine):
            async with self.engine.begin() as conn:
                await conn.execute(stmt)
        else:
            from anyio import to_thread

            engine = self.engine

            def run() -> None:
                with engine.begin() as conn:
                    conn.execute(stmt)

            await to_thread.run_sync(run)

    async def month_total(self, month: str) -> float:
        stmt = select(func.coalesce(func.sum(self.table.c.usd), 0.0)).where(self.table.c.month == month)
        if isinstance(self.engine, AsyncEngine):
            async with self.engine.connect() as conn:
                return float((await conn.execute(stmt)).scalar_one())
        from anyio import to_thread

        engine = self.engine

        def run() -> float:
            with engine.connect() as conn:
                return float(conn.execute(stmt).scalar_one())

        return await to_thread.run_sync(run)


class MonthlyBudgetExceeded(BudgetExceededError):
    """The app's AI budget for this month is used up. ``create_nexus_app`` renders it as HTTP 429."""

    def __init__(self, month: str, spent_usd: float, cap_usd: float) -> None:
        self.month = month
        self.spent_usd = spent_usd
        self.cap_usd = cap_usd
        super().__init__(f"Monthly AI budget reached for {month}: {spent_usd:.4f} of {cap_usd:.2f} USD")


class SpendLedgerUnavailable(MonthlyBudgetExceeded):
    """The ledger could not be read and the budget fails closed. Rendered as HTTP 503."""

    def __init__(self, month: str, cap_usd: float) -> None:
        BudgetExceededError.__init__(self, f"AI spend ledger unavailable for {month}; billed calls are paused")
        self.month = month
        self.spent_usd = float("nan")
        self.cap_usd = cap_usd


class MonthlyBudget:
    """Monthly cap over a ``SpendLedger``.

    * ``ensure_within_budget()`` raises ``MonthlyBudgetExceeded`` once the month's total reaches the
      cap. The decision is cached for ``cache_seconds`` so the ledger is not summed on every call;
      ``record`` clears the cache. The overshoot is at most the calls in flight.
    * If the ledger cannot be read, ``fail_closed=True`` (default) refuses the call with
      ``SpendLedgerUnavailable``: an outage of the ledger must not turn into unlimited spend. Set
      False to allow calls instead.
    * ``record`` is best effort by default (a failure is logged, the request goes on); pass
      ``strict=True`` to raise instead.
    """

    def __init__(
        self,
        ledger: SpendLedger,
        cap_usd: float,
        *,
        cache_seconds: float = 20.0,
        fail_closed: bool = True,
        strict: bool = False,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.ledger = ledger
        self.cap_usd = float(cap_usd)
        self.cache_seconds = cache_seconds
        self.fail_closed = fail_closed
        self.strict = strict
        self.clock = clock or (lambda: datetime.now(UTC))
        self._cache: tuple[str, float, float] | None = None  # (month, total, monotonic time)

    @property
    def unlimited(self) -> bool:
        return self.cap_usd <= 0

    async def _total(self, month: str) -> float:
        cached = self._cache
        if cached is not None and cached[0] == month and time.monotonic() - cached[2] < self.cache_seconds:
            return cached[1]
        total = await self.ledger.month_total(month)
        self._cache = (month, total, time.monotonic())
        return total

    async def ensure_within_budget(self) -> None:
        """Raise ``MonthlyBudgetExceeded`` when this month's spend has reached the cap."""
        if self.unlimited:
            return
        month = month_of(self.clock())
        try:
            total = await self._total(month)
        except Exception:
            if not self.fail_closed:
                logger.exception("could not read the AI spend ledger; allowing the call (fail open)")
                return
            logger.exception("could not read the AI spend ledger; refusing the call (fail closed)")
            raise SpendLedgerUnavailable(month, self.cap_usd) from None
        if total >= self.cap_usd:
            logger.warning("monthly AI budget reached: %.4f of %.2f USD in %s", total, self.cap_usd, month)
            raise MonthlyBudgetExceeded(month, total, self.cap_usd)

    async def record(self, usd: float, model: str, task: str = "", subject: str | None = None) -> None:
        """Append one billed call (ignored when ``usd`` is 0 or less)."""
        if usd <= 0:
            return
        entry = SpendEntry(usd=float(usd), model=model, task=task, subject=subject, at=self.clock())
        try:
            await self.ledger.record(entry)
        except Exception:
            if self.strict:
                raise
            logger.exception("failed to record AI spend (%.6f USD, %s)", usd, model)
            return
        finally:
            self._cache = None

    async def summary(self) -> dict[str, Any]:
        """``month``, ``spent_usd``, ``cap_usd`` (None when unlimited), ``remaining_usd``, ``over_budget``."""
        month = month_of(self.clock())
        total = await self.ledger.month_total(month)
        if self.unlimited:
            return {
                "month": month,
                "spent_usd": round(total, 6),
                "cap_usd": None,
                "remaining_usd": None,
                "over_budget": False,
            }
        return {
            "month": month,
            "spent_usd": round(total, 6),
            "cap_usd": self.cap_usd,
            "remaining_usd": round(max(self.cap_usd - total, 0.0), 6),
            "over_budget": total >= self.cap_usd,
        }
