"""`nexus new` scaffold: runs the CLI into a temp dir and checks the app builds, starts and tests green."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from nexus.cli.main import main, scaffold_new_app
from nexus.qa.runner import run_generated_tests
from nexus.teams.it_pack.platform_templates import CONTAINER_PORT, FRAMEWORK_PACKAGE


def _run_cli(monkeypatch: pytest.MonkeyPatch, *argv: str) -> None:
    monkeypatch.setattr(sys, "argv", ["nexus", *argv])
    main()


def _dockerfile_cmd(dockerfile: str) -> list[str]:
    line = next(ln for ln in dockerfile.splitlines() if ln.startswith("CMD "))
    cmd = json.loads(line[len("CMD ") :])
    assert isinstance(cmd, list)
    return [str(part) for part in cmd]


def test_nexus_new_scaffolds_a_working_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_cli(monkeypatch, "new", "demo-app", "--output-dir", str(tmp_path))
    app_dir = tmp_path / "demo-app"

    # The package is importable (dash replaced by underscore) and holds main.py.
    main_py = app_dir / "src" / "demo_app" / "main.py"
    assert main_py.is_file()
    assert (app_dir / "src" / "demo_app" / "__init__.py").is_file()
    assert "app, db = create_nexus_app(" in main_py.read_text(encoding="utf-8")

    # The Dockerfile CMD points at that module, resolved against src/.
    dockerfile = (app_dir / "Dockerfile").read_text(encoding="utf-8")
    cmd = _dockerfile_cmd(dockerfile)
    assert cmd[0] == "uvicorn"
    module, attr = cmd[1].split(":")
    app_dir_arg = cmd[cmd.index("--app-dir") + 1]
    assert attr == "app"
    assert (app_dir / app_dir_arg / Path(*module.split("."))).with_suffix(".py") == main_py
    assert cmd[cmd.index("--port") + 1] == str(CONTAINER_PORT)

    # Non root runtime user, port 8080, only requirements and src copied in.
    assert re.search(r"^USER 10001:10001$", dockerfile, re.MULTILINE)
    assert f"EXPOSE {CONTAINER_PORT}" in dockerfile
    assert "COPY requirements.txt ./" in dockerfile
    assert "COPY . ." not in dockerfile
    assert "tests/" in (app_dir / ".dockerignore").read_text(encoding="utf-8")
    assert (app_dir / "requirements.txt").read_text(encoding="utf-8").startswith(f"{FRAMEWORK_PACKAGE}>=")

    pyproject = (app_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "demo-app"' in pyproject
    assert 'packages = ["src/demo_app"]' in pyproject
    assert 'pythonpath = ["src"]' in pyproject

    # The generated app's own tests pass (no model call: the client is a dependency override).
    result = run_generated_tests(app_dir, timeout_s=120)
    assert result.executed
    assert result.passed, result.output_tail
    assert result.tests_passed == 2


@pytest.mark.parametrize("bad_name", ["../escape", "1app", "", "my app", "a/b", "x" * 41])
def test_scaffold_rejects_unsafe_names(tmp_path: Path, bad_name: str) -> None:
    with pytest.raises(ValueError, match="Invalid app name"):
        scaffold_new_app(bad_name, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_nexus_new_reports_errors_with_exit_code(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "taken").mkdir()
    with pytest.raises(SystemExit) as exc:
        _run_cli(monkeypatch, "new", "taken", "--output-dir", str(tmp_path))
    assert exc.value.code == 2
