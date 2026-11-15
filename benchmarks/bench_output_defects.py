"""Defect injection benchmark: how robust is the squad pipeline to realistic model output defects?

Real models return structured output whose code fields are often not clean source files: wrapped in
markdown fences, surrounded by prose, double escaped, with Windows line endings, or with imports that
assume a different package layout. This benchmark takes the deterministic showcase squad (whose
clean output passes end to end) and injects exactly one such defect into the code it returns, then
runs the pipeline with self healing OFF and records whether the generated suite passes first time.

It measures what the pipeline itself absorbs (sanitizing and writing code), independent of any
model, at zero cost. A defect counts as handled when the generated tests pass for every idea.

Usage::

    python benchmarks/bench_output_defects.py
    python benchmarks/bench_output_defects.py --ideas 2 --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "apps" / "showcase" / "backend" / "src", ROOT / "benchmarks"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from bench_generation import IDEAS, check_builds  # noqa: E402

from nexus.providers.base import BaseModelProvider, ModelResponse  # noqa: E402
from nexus.teams.it_pack import NexusITTeam  # noqa: E402
from nexus.teams.it_pack.fullstack import FullStackSpecification  # noqa: E402
from nexus.teams.it_pack.qa import QaSpecification  # noqa: E402

T = TypeVar("T", bound=BaseModel)
Transform = Callable[[str], str]


def _fence(code: str) -> str:
    return f"```python\n{code.strip()}\n```"


def _prose(code: str) -> str:
    return f"Here is the complete file:\n\n```python\n{code.strip()}\n```\n\nThis implements the requested endpoints."


def _escaped(code: str) -> str:
    return code.replace("\n", "\\n")


def _rel_imports(code: str) -> str:
    return re.sub(r"^from (models|backend_models) import", r"from .\1 import", code, flags=re.M)


def _src_import(code: str) -> str:
    return re.sub(r"^from main import", "from src.main import", code, flags=re.M)


def _pkg_import(code: str) -> str:
    return re.sub(r"^from main import", "from backend.src.main import", code, flags=re.M)


def _app_import(code: str) -> str:
    return re.sub(r"^from main import", "from app.main import", code, flags=re.M)


def _drop_testclient_import(code: str) -> str:
    return re.sub(r"^from fastapi\.testclient import TestClient\n", "", code, flags=re.M)


def _language_tag_only(code: str) -> str:
    return f"python\n{code}"


def _trailing_fence_only(code: str) -> str:
    return f"{code.rstrip()}\n```"


# name -> (applies to backend code, applies to tests, transform)
DEFECTS: dict[str, tuple[bool, bool, Transform]] = {
    "clean (control)": (True, True, lambda c: c),
    "markdown fence": (True, True, _fence),
    "prose around fence": (True, True, _prose),
    "CRLF line endings": (True, True, lambda c: c.replace("\n", "\r\n")),
    "UTF-8 BOM": (True, True, lambda c: "﻿" + c),
    "double escaped newlines": (True, True, _escaped),
    "stray language tag line": (True, True, _language_tag_only),
    "unbalanced closing fence": (True, True, _trailing_fence_only),
    "relative model imports": (True, False, _rel_imports),
    "tests: from src.main": (False, True, _src_import),
    "tests: from backend.src.main": (False, True, _pkg_import),
    "tests: from app.main": (False, True, _app_import),
    "tests: TestClient not imported": (False, True, _drop_testclient_import),
}


class DefectProvider(BaseModelProvider):
    """Wraps a provider and injects one defect into the code fields of the squad's output."""

    def __init__(self, inner: BaseModelProvider, backend: bool, tests: bool, transform: Transform) -> None:
        self.inner = inner
        self.backend = backend
        self.tests = tests
        self.transform = transform

    @property
    def name(self) -> str:
        return self.inner.name

    def generate(
        self, prompt: str, system_instruction: str | None = None, model: str | None = None, temperature: float = 0.2
    ) -> ModelResponse:
        return self.inner.generate(prompt, system_instruction, model, temperature)

    def structured(
        self, prompt: str, response_model: type[T], system_instruction: str | None = None, model: str | None = None
    ) -> T:
        result = self.inner.structured(prompt, response_model, system_instruction, model)
        self.last_usage = getattr(self.inner, "last_usage", None)
        if isinstance(result, FullStackSpecification) and self.backend:
            result = result.model_copy(
                update={
                    "backend_main_py": self.transform(result.backend_main_py),
                    "backend_models_py": self.transform(result.backend_models_py),
                }
            )
        if isinstance(result, QaSpecification) and self.tests:
            result = result.model_copy(update={"test_suite_code": self.transform(result.test_suite_code)})
        return result  # type: ignore[return-value]

    def converse(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> ModelResponse:
        return self.inner.converse(messages, tools, system_instruction, model)


def run(ideas: Sequence[str], defects: Sequence[str]) -> dict[str, dict[str, Any]]:
    from showcase_provider import ShowcaseSquadProvider

    results: dict[str, dict[str, Any]] = {}
    tmp_root = Path(tempfile.mkdtemp(prefix="nexus_defects_"))
    try:
        for d_index, defect in enumerate(defects):
            backend, tests, transform = DEFECTS[defect]
            passed = built = 0
            notes: list[str] = []
            for i, idea in enumerate(ideas):
                workdir = tmp_root / f"d{d_index}" / f"i{i}"
                workdir.mkdir(parents=True)
                inner = ShowcaseSquadProvider(idea=idea, target_cloud="gcp", simulate_healing=False)
                team = NexusITTeam(provider=DefectProvider(inner, backend, tests, transform))
                project = team.build_from_idea(idea, output_dir=workdir, enable_self_healing=False)
                ok = bool(project.test_run and project.test_run.passed)
                passed += ok
                backend_dir = Path(project.output_path or workdir) / "backend"
                compiles = not check_builds(backend_dir)
                built += compiles
                if not ok and project.test_run is not None and not notes:
                    tail = project.test_run.output_tail.strip().splitlines()
                    notes.append(next((ln for ln in reversed(tail) if "Error" in ln), tail[-1] if tail else "")[:140])
            results[defect] = {"ideas": len(ideas), "tests_pass": passed, "compiles": built, "first_failure": notes}
            mark = "ok  " if passed == len(ideas) else "FAIL"
            print(f"{mark} {defect:<32} tests pass {passed}/{len(ideas)}  compiles {built}/{len(ideas)}  {notes[:1]}")
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    return results


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ideas", type=int, default=3, help="use the first N ideas of the fixed set")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)
    results = run(IDEAS[: args.ideas], list(DEFECTS))
    injected = [k for k in results if k != "clean (control)"]
    handled = sum(1 for k in injected if results[k]["tests_pass"] == results[k]["ideas"])
    cases = sum(results[k]["ideas"] for k in injected)
    case_pass = sum(results[k]["tests_pass"] for k in injected)
    print(f"\nDefects fully handled: {handled}/{len(injected)}; cases passing: {case_pass}/{cases}")
    if args.json:
        args.json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
