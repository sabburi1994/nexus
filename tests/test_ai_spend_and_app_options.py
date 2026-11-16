"""nexus.ai.spend (monthly AI spend ledger) and the create_nexus_app adoption options."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from nexus.agents.context import BudgetExceededError
from nexus.ai.spend import (
    AiSpendDisabled,
    InMemorySpendLedger,
    MonthlyBudget,
    MonthlyBudgetExceeded,
    SpendEntry,
    SpendLedger,
    SpendLedgerUnavailable,
    SqlSpendLedger,
    month_of,
    parse_budget_cap,
)
from nexus.api import create_nexus_app

NOV = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)
DEC = datetime(2026, 12, 1, 0, 0, 1, tzinfo=UTC)


def test_month_of_is_utc() -> None:
    assert month_of(datetime(2026, 11, 30, 23, 30, tzinfo=UTC)) == "2026-11"
    assert month_of(datetime(2026, 12, 1, 0, 30)) == "2026-12"  # naive is treated as UTC


async def test_in_memory_ledger_sums_per_month() -> None:
    ledger = InMemorySpendLedger()
    await ledger.record(SpendEntry(0.4, "gemini", "brief", None, NOV))
    await ledger.record(SpendEntry(0.1, "gemini", "brief", "u1", NOV))
    await ledger.record(SpendEntry(9.0, "gemini", "brief", None, DEC))
    assert math.isclose(await ledger.month_total("2026-11"), 0.5)
    assert await ledger.month_total("2027-01") == 0.0


async def _exercise_sql(ledger: SqlSpendLedger) -> None:
    await ledger.create_table()
    await ledger.create_table()  # idempotent
    await ledger.record(SpendEntry(0.25, "gemini-3.8-flash", "analysis", "learner-7", NOV))
    await ledger.record(SpendEntry(0.5, "gemini-3.8-flash", "analysis" * 40, None, NOV))  # long text is cut
    await ledger.record(SpendEntry(1.0, "gemini-3.8-flash", "analysis", None, DEC))
    assert math.isclose(await ledger.month_total("2026-11"), 0.75)
    assert math.isclose(await ledger.month_total("2026-12"), 1.0)
    assert await ledger.month_total("2025-01") == 0.0


async def test_sql_ledger_with_a_sync_engine(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'spend.db'}")
    try:
        await _exercise_sql(SqlSpendLedger(engine))
    finally:
        engine.dispose()


async def test_sql_ledger_with_an_async_engine(tmp_path: Path) -> None:
    pytest.importorskip("aiosqlite")
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'spend_async.db'}")
    try:
        await _exercise_sql(SqlSpendLedger(engine))
    finally:
        await engine.dispose()


async def test_budget_allows_until_the_cap_then_refuses() -> None:
    clock = [NOV]
    budget = MonthlyBudget(InMemorySpendLedger(), cap_usd=1.0, clock=lambda: clock[0])
    await budget.ensure_within_budget()
    await budget.record(0.6, "gemini", "brief")
    await budget.ensure_within_budget()  # 0.6 < 1.0
    await budget.record(0.4, "gemini", "brief")  # record clears the cached decision
    with pytest.raises(MonthlyBudgetExceeded) as exceeded:
        await budget.ensure_within_budget()
    assert exceeded.value.month == "2026-11" and math.isclose(exceeded.value.spent_usd, 1.0)
    assert isinstance(exceeded.value, BudgetExceededError)
    summary = await budget.summary()
    assert summary == {"month": "2026-11", "spent_usd": 1.0, "cap_usd": 1.0, "remaining_usd": 0.0, "over_budget": True}
    clock[0] = DEC  # a new month starts from zero
    await budget.ensure_within_budget()
    assert (await budget.summary())["spent_usd"] == 0.0


async def test_budget_caches_the_decision_between_records() -> None:
    class Counting(InMemorySpendLedger):
        reads = 0

        async def month_total(self, month: str) -> float:
            Counting.reads += 1
            return await super().month_total(month)

    budget = MonthlyBudget(Counting(), cap_usd=5.0, clock=lambda: NOV, cache_seconds=60)
    for _ in range(5):
        await budget.ensure_within_budget()
    assert Counting.reads == 1


async def test_none_cap_is_unlimited_and_zero_spend_is_not_recorded() -> None:
    ledger = InMemorySpendLedger()
    budget = MonthlyBudget(ledger, cap_usd=None, clock=lambda: NOV)
    assert budget.unlimited and not budget.disabled
    await budget.record(0.0, "gemini")
    await budget.record(-1.0, "gemini")
    assert ledger.entries == []
    await budget.record(50.0, "gemini")
    await budget.ensure_within_budget()
    assert (await budget.summary())["cap_usd"] is None


async def test_zero_cap_switches_ai_off_without_reading_the_ledger() -> None:
    """0 means no AI at all (TandemPath's kill switch), never unlimited."""
    budget = MonthlyBudget(BrokenLedger(), cap_usd=0, clock=lambda: NOV)
    assert budget.disabled and not budget.unlimited
    with pytest.raises(AiSpendDisabled) as refused:
        await budget.ensure_within_budget()
    assert isinstance(refused.value, MonthlyBudgetExceeded) and refused.value.month == "2026-11"
    with pytest.raises(AiSpendDisabled):
        budget.ensure_within_budget_sync()


@pytest.mark.parametrize("bad", [-0.01, -5, "-1", float("nan"), "ten"])
def test_negative_or_invalid_cap_is_a_configuration_error(bad: object) -> None:
    with pytest.raises(ValueError):
        MonthlyBudget(InMemorySpendLedger(), cap_usd=bad)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("raw", "cap"),
    [(None, None), ("", None), (" none ", None), ("Unlimited", None), ("0", 0.0), ("12.5", 12.5), (10, 10.0)],
)
def test_parse_budget_cap_reads_configuration(raw: object, cap: float | None) -> None:
    assert parse_budget_cap(raw) == cap  # type: ignore[arg-type]


def test_sync_api_matches_the_async_one(tmp_path: Path) -> None:
    clock = [NOV]
    engine = create_engine(f"sqlite:///{tmp_path / 'sync_spend.db'}")
    try:
        ledger = SqlSpendLedger(engine)
        ledger.table.create(engine, checkfirst=True)
        budget = MonthlyBudget(ledger, cap_usd=1.0, clock=lambda: clock[0])
        budget.ensure_within_budget_sync()
        budget.record_sync(0.6, "gemini", "brief", "user-1")
        budget.ensure_within_budget_sync()
        budget.record_sync(0.4, "gemini", "brief")
        with pytest.raises(MonthlyBudgetExceeded):
            budget.ensure_within_budget_sync()
        assert budget.summary_sync() == {
            "month": "2026-11",
            "spent_usd": 1.0,
            "cap_usd": 1.0,
            "remaining_usd": 0.0,
            "over_budget": True,
        }
        clock[0] = DEC
        budget.ensure_within_budget_sync()
    finally:
        engine.dispose()


async def test_sync_api_needs_a_sync_ledger(tmp_path: Path) -> None:
    pytest.importorskip("aiosqlite")
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'async_only.db'}")
    try:
        budget = MonthlyBudget(SqlSpendLedger(engine), cap_usd=1.0, clock=lambda: NOV)
        with pytest.raises(NotImplementedError, match="sync Engine"):
            budget.ensure_within_budget_sync()
        with pytest.raises(NotImplementedError):
            budget.record_sync(0.1, "gemini")
    finally:
        await engine.dispose()


def test_sync_api_fails_closed_and_records_best_effort() -> None:
    class BrokenSync(InMemorySpendLedger):
        def month_total_sync(self, month: str) -> float:
            raise RuntimeError("database down")

        def record_sync(self, entry: SpendEntry) -> None:
            raise RuntimeError("database down")

    with pytest.raises(SpendLedgerUnavailable):
        MonthlyBudget(BrokenSync(), cap_usd=1.0, clock=lambda: NOV).ensure_within_budget_sync()
    MonthlyBudget(BrokenSync(), cap_usd=1.0, clock=lambda: NOV, fail_closed=False).ensure_within_budget_sync()
    MonthlyBudget(BrokenSync(), cap_usd=1.0, clock=lambda: NOV).record_sync(0.1, "gemini")
    with pytest.raises(RuntimeError):
        MonthlyBudget(BrokenSync(), cap_usd=1.0, clock=lambda: NOV, strict=True).record_sync(0.1, "gemini")


class BrokenLedger(SpendLedger):
    async def record(self, entry: SpendEntry) -> None:
        raise RuntimeError("database down")

    async def month_total(self, month: str) -> float:
        raise RuntimeError("database down")


async def test_unreadable_ledger_fails_closed_by_default_and_open_on_request() -> None:
    with pytest.raises(SpendLedgerUnavailable):
        await MonthlyBudget(BrokenLedger(), cap_usd=1.0, clock=lambda: NOV).ensure_within_budget()
    await MonthlyBudget(BrokenLedger(), cap_usd=1.0, clock=lambda: NOV, fail_closed=False).ensure_within_budget()


async def test_record_is_best_effort_unless_strict() -> None:
    await MonthlyBudget(BrokenLedger(), cap_usd=1.0, clock=lambda: NOV).record(0.1, "gemini")
    with pytest.raises(RuntimeError):
        await MonthlyBudget(BrokenLedger(), cap_usd=1.0, clock=lambda: NOV, strict=True).record(0.1, "gemini")


# create_nexus_app: error contract for budget errors, docs and health options ---------------------


def test_budget_errors_render_the_nexus_error_contract() -> None:
    app = create_nexus_app(title="Budget")
    exhausted = MonthlyBudget(InMemorySpendLedger(), cap_usd=0.5, clock=lambda: NOV)
    unavailable = MonthlyBudget(BrokenLedger(), cap_usd=0.5, clock=lambda: NOV)
    switched_off = MonthlyBudget(InMemorySpendLedger(), cap_usd=0, clock=lambda: NOV)

    @app.post("/api/ask")
    async def ask() -> dict[str, bool]:
        await exhausted.record(1.0, "gemini")
        await exhausted.ensure_within_budget()
        return {"ok": True}

    @app.post("/api/ask-broken")
    async def ask_broken() -> dict[str, bool]:
        await unavailable.ensure_within_budget()
        return {"ok": True}

    @app.post("/api/ask-off")
    async def ask_off() -> dict[str, bool]:
        await switched_off.ensure_within_budget()
        return {"ok": True}

    client = TestClient(app)
    resp = client.post("/api/ask", headers={"X-Request-ID": "req-9"})
    assert resp.status_code == 429
    assert resp.json() == {
        "error": "ai_budget_exhausted",
        "message": "The monthly AI budget is used up. AI features resume next month.",
        "month": "2026-11",
        "request_id": "req-9",
    }
    broken = client.post("/api/ask-broken")
    assert broken.status_code == 503 and broken.json()["error"] == "ai_budget_unavailable"
    off = client.post("/api/ask-off")
    assert off.status_code == 429
    assert off.json()["error"] == "ai_disabled"
    assert off.json()["message"] == "AI features are switched off for this app."
    assert "database" not in broken.text


def test_docs_can_be_turned_off_and_probe_paths_kept() -> None:
    app = create_nexus_app(title="Private", docs=False, health_path="/healthz", ready_path=None)
    client = TestClient(app)
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    assert client.get("/healthz").json()["status"] == "ok"
    assert client.head("/healthz").status_code == 200
    assert client.get("/health").status_code == 404
    assert client.get("/ready").status_code == 404

    default = TestClient(create_nexus_app(title="Public"))
    assert default.get("/docs").status_code == 200
    assert default.get("/ready").json() == {"status": "ready"}
