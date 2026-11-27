"""Tests for Alembic migration and HS256 bearer auth starter templates."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from nexus.cli.main import main
from nexus.providers.mock import MockProvider
from nexus.qa.runner import run_generated_tests
from nexus.teams.it_pack import NexusITTeam
from nexus.teams.it_pack import platform_templates as tpl


def _run_cli(monkeypatch: pytest.MonkeyPatch, *argv: str) -> None:
    monkeypatch.setattr(sys, "argv", ["nexus", *argv])
    main()


def test_alembic_templates_are_valid_and_read_database_url() -> None:
    files = tpl.render_alembic_files("demo_app.models")
    assert set(files) == {
        "alembic.ini",
        "migrations/env.py",
        "migrations/script.py.mako",
        "migrations/versions/.gitkeep",
    }
    assert "script_location = migrations" in files["alembic.ini"]
    assert "sqlalchemy.url" not in files["alembic.ini"]
    ast.parse(files["migrations/env.py"])
    assert 'os.getenv("DATABASE_URL"' in files["migrations/env.py"]
    assert 'importlib.import_module("demo_app.models")' in files["migrations/env.py"]


def test_auth_template_compiles_cleanly() -> None:
    src = tpl.render_auth_module()
    ast.parse(src)
    assert "hmac.compare_digest" in src
    assert "AUTH_SECRET" in src


def test_nexus_new_with_migrations_and_auth_passes_generated_tests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _run_cli(monkeypatch, "new", "secure-app", "--output-dir", str(tmp_path), "--with-migrations", "--with-auth")
    app_dir = tmp_path / "secure-app"

    assert (app_dir / "alembic.ini").is_file()
    assert (app_dir / "migrations" / "env.py").is_file()
    assert (app_dir / "migrations" / "script.py.mako").is_file()
    assert (app_dir / "src" / "secure_app" / "auth.py").is_file()
    assert "alembic>=1.13.0" in (app_dir / "requirements.txt").read_text(encoding="utf-8")
    assert '"alembic>=1.13.0"' in (app_dir / "pyproject.toml").read_text(encoding="utf-8")

    # Generated test suite (including test_auth.py checking 401/expired/tampered/valid HS256 JWTs) passes for real.
    result = run_generated_tests(app_dir, timeout_s=120)
    assert result.executed
    assert result.passed, result.output_tail
    assert result.tests_passed == 3


def test_it_squad_writes_alembic_and_optional_auth(tmp_path: Path) -> None:
    project = NexusITTeam(
        provider=MockProvider(),
        run_generated_tests=False,
        include_auth=True,
    ).build_from_idea("A vendor invoice tracker", output_dir=tmp_path, enable_self_healing=False)

    backend = Path(project.output_path or "") / "backend"
    assert (backend / "alembic.ini").is_file()
    assert (backend / "migrations" / "env.py").is_file()
    assert (backend / "src" / "auth.py").is_file()
