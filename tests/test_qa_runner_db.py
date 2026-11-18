"""Every generated test run gets a fresh database (found by the real model benchmark).

The healing loop rewrites the models between runs and SQLAlchemy's ``create_all`` never alters an
existing table, so a database left by an earlier run failed with "no such column".
"""

from __future__ import annotations

from pathlib import Path

from nexus.qa.runner import run_generated_tests

SUITE = """
import os
import sqlite3
from pathlib import Path


def test_database_is_fresh_and_outside_the_workspace():
    url = os.environ["DATABASE_URL"]
    assert url.startswith("sqlite:///")
    path = Path(url.removeprefix("sqlite:///"))
    assert not path.exists(), "a database from an earlier run was reused"
    assert Path.cwd() not in path.parents
    with sqlite3.connect(path) as db:
        db.execute("create table items (id integer primary key)")
"""


def test_each_run_gets_an_empty_database_that_is_removed_afterwards(tmp_path: Path) -> None:
    backend = tmp_path / "backend"
    (backend / "tests").mkdir(parents=True)
    (backend / "src").mkdir()
    (backend / "tests" / "test_db.py").write_text(SUITE, encoding="utf-8")
    first = run_generated_tests(backend)
    second = run_generated_tests(backend)
    assert first.passed, first.output_tail
    assert second.passed, second.output_tail
    assert not list(backend.rglob("*.db"))
