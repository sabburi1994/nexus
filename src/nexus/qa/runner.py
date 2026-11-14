"""Nexus QA: run a generated pytest suite for real in a subprocess.

This executes model generated code on the local machine. It is bounded by a timeout and runs
with a reduced environment (no cloud credentials or API keys from the parent process), but it
is not a sandbox: only run it on workspaces whose generator you trust, never on code a remote
visitor can steer.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_TEST_TIMEOUT_S = 120.0
_OUTPUT_TAIL_CHARS = 4000

# Variables the interpreter and pytest need; everything else (credentials, API keys,
# cloud project settings) stays out of the generated code's environment.
_PASSTHROUGH_ENV = (
    "PATH",
    "SYSTEMROOT",
    "SYSTEMDRIVE",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "TEMP",
    "TMP",
    "TMPDIR",
    "HOME",
    "USERPROFILE",
    "LANG",
    "LC_ALL",
    "VIRTUAL_ENV",
)

_SUMMARY_COUNT = re.compile(r"(\d+) (passed|failed|errors?|skipped)")


class TestRunResult(BaseModel):
    """Outcome of one real pytest run against a generated workspace."""

    __test__ = False  # not a pytest test class

    executed: bool = Field(description="True if pytest was started")
    passed: bool = Field(description="True only if pytest exited 0")
    exit_code: int | None = None
    timed_out: bool = False
    tests_passed: int = 0
    tests_failed: int = 0
    tests_errored: int = 0
    duration_s: float = 0.0
    command: str = ""
    output_tail: str = Field(default="", description="Last part of the combined pytest output")

    @property
    def summary(self) -> str:
        if not self.executed:
            return "generated tests not executed"
        if self.timed_out:
            return f"generated tests timed out after {self.duration_s:.0f}s"
        if self.exit_code == 5:
            return "no tests collected from the generated suite"
        counts = f"{self.tests_passed} passed, {self.tests_failed} failed, {self.tests_errored} errors"
        return f"generated tests {'passed' if self.passed else 'FAILED'} ({counts}, exit {self.exit_code})"


def _child_env(backend_dir: Path) -> dict[str, str]:
    env = {k: v for k in _PASSTHROUGH_ENV if (v := os.environ.get(k)) is not None}
    env["PYTHONPATH"] = str(backend_dir / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _parse_counts(output: str) -> tuple[int, int, int]:
    passed = failed = errored = 0
    for num, kind in _SUMMARY_COUNT.findall(output):
        if kind == "passed":
            passed = int(num)
        elif kind == "failed":
            failed = int(num)
        elif kind.startswith("error"):
            errored = int(num)
    return passed, failed, errored


def run_generated_tests(backend_dir: Path, timeout_s: float = DEFAULT_TEST_TIMEOUT_S) -> TestRunResult:
    """Run ``pytest tests`` inside ``backend_dir`` (the generated ``backend/`` folder).

    Uses the current interpreter, so the generated suite sees the same installed packages
    (``nexus-agent-framework``, ``fastapi``, ``httpx``) as the caller.
    """
    backend_dir = backend_dir.resolve()
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        f"--rootdir={backend_dir}",
        f"--confcutdir={backend_dir}",
    ]
    command = " ".join(cmd[1:])
    if not (backend_dir / "tests").is_dir():
        return TestRunResult(executed=False, passed=False, command=command, output_tail="no tests/ directory")

    started = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=backend_dir,
            env=_child_env(backend_dir),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        return TestRunResult(
            executed=True,
            passed=False,
            timed_out=True,
            duration_s=time.perf_counter() - started,
            command=command,
            output_tail=partial[-_OUTPUT_TAIL_CHARS:],
        )
    except OSError as exc:
        return TestRunResult(
            executed=False, passed=False, command=command, output_tail=f"could not start pytest: {exc}"
        )

    output = (proc.stdout or "") + (proc.stderr or "")
    passed_n, failed_n, errored_n = _parse_counts(output)
    return TestRunResult(
        executed=True,
        passed=proc.returncode == 0,
        exit_code=proc.returncode,
        tests_passed=passed_n,
        tests_failed=failed_n,
        tests_errored=errored_n,
        duration_s=time.perf_counter() - started,
        command=command,
        output_tail=output[-_OUTPUT_TAIL_CHARS:],
    )
