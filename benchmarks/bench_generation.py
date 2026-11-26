"""Generation benchmark: end to end accuracy and per stage cost of ``NexusITTeam.build_from_idea``.

For a fixed set of ideas it runs the full squad, writes each workspace to a temporary folder and
then checks the result independently of the squad's own verdict:

* **builds**: every generated backend ``.py`` file compiles;
* **starts**: ``uvicorn main:app --app-dir src`` boots and ``GET /health`` returns 200;
* **tests pass**: the generated pytest suite passes (the real run the QA gate used).

It also reports wall time per squad stage, prompt and output size per stage (characters, and
estimated tokens at 4 characters per token, model independent), real input/output tokens and cost
as reported by the provider, and the number of healing cycles.

Providers (no paid model calls unless you pass one explicitly):

* ``deterministic``: the showcase's idea aware deterministic squad (realistic code, includes one
  intentional QA failure so self healing runs);
* ``mock``: ``MockProvider`` (placeholder output), the floor;
* ``vertex``: a real Gemini model on Vertex AI (**paid**). Needs ``--project`` (or
  ``GCP_PROJECT_ID``) and ``gcloud auth login``. Spend is counted from every HTTP response's
  ``usageMetadata`` (input, output and thinking tokens, failed parses included) at the prices given
  by ``--price-in`` and ``--price-out``; the run stops before a call once ``--max-spend-usd`` (whole
  run) or ``--per-idea-spend-usd`` (one idea) is reached.

This executes generated code on this machine (pytest and uvicorn in subprocesses with a reduced
environment). Only run it on providers you trust.

Usage::

    python benchmarks/bench_generation.py                       # deterministic + mock
    python benchmarks/bench_generation.py --providers deterministic --json out.json
    python benchmarks/bench_generation.py --providers vertex --project my-project --max-spend-usd 8
"""

from __future__ import annotations

import argparse
import json
import os
import py_compile
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
SHOWCASE_SRC = ROOT / "apps" / "showcase" / "backend" / "src"
for p in (ROOT / "src", SHOWCASE_SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from nexus.providers.base import BaseModelProvider, ModelResponse  # noqa: E402
from nexus.providers.mock import MockProvider  # noqa: E402
from nexus.qa import runner as qa_runner  # noqa: E402
from nexus.teams.it_pack import NexusITTeam  # noqa: E402
from nexus.teams.it_pack import platform_templates as tpl  # noqa: E402

T = TypeVar("T", bound=BaseModel)

# Fixed idea set. Keep it stable so numbers are comparable across PRs; add new ideas at the end.
IDEAS: tuple[str, ...] = (
    "Treasury ledger triage service for disputed invoices",
    "Track second hand luxury watches in Europe with price alerts",
    "Volunteer shift scheduler for a community food bank",
    "Clinic appointment reminders with no-show statistics",
    "Bike sharing station availability dashboard",
    "Recipe cost calculator for small restaurants",
    "Internal IT asset inventory with warranty expiry alerts",
    "Language exchange partner matching for students",
)


@dataclass
class StageStat:
    calls: int = 0
    seconds: float = 0.0
    prompt_chars: int = 0
    output_chars: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class InstrumentedProvider(BaseModelProvider):
    """Wraps a provider and records time, sizes and reported usage per response model (stage)."""

    def __init__(self, inner: BaseModelProvider) -> None:
        self.inner = inner
        self.stages: dict[str, StageStat] = defaultdict(StageStat)

    @property
    def name(self) -> str:
        return self.inner.name

    def _account(self, stage: str, started: float, prompt: str, system: str | None, output: str) -> None:
        st = self.stages[stage]
        st.calls += 1
        st.seconds += time.perf_counter() - started
        st.prompt_chars += len(prompt) + len(system or "")
        st.output_chars += len(output)
        usage = getattr(self.inner, "last_usage", None)
        self.last_usage = usage
        if usage is not None:
            st.input_tokens += int(getattr(usage, "input_tokens", 0))
            st.output_tokens += int(getattr(usage, "output_tokens", 0))
            st.cost_usd += float(getattr(usage, "cost_usd", 0.0))

    def generate(
        self, prompt: str, system_instruction: str | None = None, model: str | None = None, temperature: float = 0.2
    ) -> ModelResponse:
        started = time.perf_counter()
        resp = self.inner.generate(prompt, system_instruction, model, temperature)
        st = self.stages["generate"]
        st.calls += 1
        st.seconds += time.perf_counter() - started
        st.prompt_chars += len(prompt) + len(system_instruction or "")
        st.output_chars += len(resp.text)
        st.input_tokens += resp.input_tokens
        st.output_tokens += resp.output_tokens
        st.cost_usd += resp.cost_usd
        return resp

    def structured(
        self, prompt: str, response_model: type[T], system_instruction: str | None = None, model: str | None = None
    ) -> T:
        started = time.perf_counter()
        result = self.inner.structured(prompt, response_model, system_instruction, model)
        self._account(response_model.__name__, started, prompt, system_instruction, result.model_dump_json())
        return result

    def converse(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        system_instruction: str | None = None,
        model: str | None = None,
    ) -> ModelResponse:
        return self.inner.converse(messages, tools, system_instruction, model)


class SpendCapReached(RuntimeError):
    """The benchmark's own spend cap stopped a paid model call."""


@dataclass
class SpendGuard:
    """Counts paid model spend from raw Vertex AI responses and refuses calls past the caps.

    It hooks ``GeminiClient._post``, so every billed response is counted, including structured
    calls whose JSON then fails to parse (the provider's own usage report misses those).
    """

    max_total_usd: float
    max_idea_usd: float
    price_in_per_m: float
    price_out_per_m: float
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    token_refreshes: int = 0
    idea_start_usd: float = 0.0

    @property
    def spent_usd(self) -> float:
        out = self.output_tokens + self.thinking_tokens
        return (self.input_tokens * self.price_in_per_m + out * self.price_out_per_m) / 1_000_000.0

    def start_idea(self) -> None:
        self.idea_start_usd = self.spent_usd

    def idea_spent_usd(self) -> float:
        return self.spent_usd - self.idea_start_usd

    def check(self) -> None:
        if self.spent_usd >= self.max_total_usd:
            raise SpendCapReached(f"run spend cap reached: {self.spent_usd:.4f} of {self.max_total_usd:.2f} USD")
        if self.idea_spent_usd() >= self.max_idea_usd:
            raise SpendCapReached(f"idea spend cap reached: {self.idea_spent_usd():.4f} of {self.max_idea_usd:.2f} USD")

    def attach(self, client: Any) -> None:
        original = client._post

        def guarded_post(url: str, headers: dict[str, str], body: dict[str, Any], max_retries: int = 2) -> Any:
            self.check()
            resp = original(url, headers=headers, body=body, max_retries=max_retries)
            if resp.status_code == 401 and "Authorization" in headers:
                # Workaround for a framework bug: nexus.ai.client caches an access token for 40 minutes
                # from when it fetched it, not until it expires, so long runs get 401s. Fetch a fresh
                # token and retry once (a 401 is not billed).
                from nexus.ai import client as ai_client

                ai_client._CACHED_TOKEN = None
                token = ai_client.get_gcp_access_token()
                if token:
                    self.token_refreshes += 1
                    headers = {**headers, "Authorization": f"Bearer {token}"}
                    resp = original(url, headers=headers, body=body, max_retries=max_retries)
            self.calls += 1
            try:
                usage = resp.json().get("usageMetadata", {})
            except ValueError:
                usage = {}
            self.input_tokens += int(usage.get("promptTokenCount", 0))
            self.output_tokens += int(usage.get("candidatesTokenCount", 0))
            self.thinking_tokens += int(usage.get("thoughtsTokenCount", 0))
            return resp

        client._post = guarded_post


@dataclass
class IdeaResult:
    provider: str
    idea: str
    app_dir: str = ""
    builds: bool = False
    compile_errors: list[str] = field(default_factory=list)
    starts: bool = False
    start_seconds: float | None = None
    tests_pass: bool = False
    tests_passed: int = 0
    tests_failed: int = 0
    qa_gate: bool = False
    healing_cycles: int = 0
    end_to_end: bool = False
    total_seconds: float = 0.0
    generation_seconds: float = 0.0
    test_run_seconds: float = 0.0
    test_runs: int = 0
    stages: dict[str, dict[str, float]] = field(default_factory=dict)
    spend_usd: float = 0.0
    error: str = ""


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def check_builds(backend_dir: Path) -> list[str]:
    errors: list[str] = []
    for py in sorted(backend_dir.rglob("*.py")):
        try:
            py_compile.compile(str(py), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{py.relative_to(backend_dir)}: {exc.msg.splitlines()[-1] if exc.msg else exc}")
    return errors


def check_starts(backend_dir: Path, timeout_s: float = 20.0) -> tuple[bool, float | None]:
    port = _free_port()
    env = qa_runner._child_env(backend_dir)
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--app-dir", "src", "--host", "127.0.0.1", "--port", str(port)]
    started = time.perf_counter()
    proc = subprocess.Popen(
        cmd, cwd=backend_dir, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        while time.perf_counter() - started < timeout_s:
            if proc.poll() is not None:
                return False, None
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as resp:  # noqa: S310
                    if resp.status == 200:
                        return True, time.perf_counter() - started
            except OSError:
                time.sleep(0.1)
        return False, None
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def _provider_factory(
    name: str, project: str | None = None, model: str | None = None, guard: SpendGuard | None = None
) -> Callable[[str], BaseModelProvider]:
    if name == "deterministic":
        from showcase_provider import ShowcaseSquadProvider

        return lambda idea: ShowcaseSquadProvider(idea=idea, target_cloud="gcp", simulate_healing=True)
    if name == "mock":
        return lambda idea: MockProvider()
    if name == "vertex":
        if guard is None:
            raise SystemExit("the vertex provider needs a spend guard")
        if not project:
            raise SystemExit("the vertex provider needs --project (or GCP_PROJECT_ID)")
        from nexus.providers.vertex import VertexAIProvider

        def make(idea: str) -> BaseModelProvider:
            provider = VertexAIProvider(project_id=project, default_model=model or "gemini-3.8-flash")
            guard.attach(provider._client)
            return provider

        return make
    raise SystemExit(f"unknown provider {name!r} (choose deterministic, mock or vertex)")


def run_one(
    provider_name: str,
    idea: str,
    workdir: Path,
    max_healing_cycles: int,
    factory: Callable[[str], BaseModelProvider] | None = None,
    guard: SpendGuard | None = None,
    squad_budget_usd: float | None = None,
) -> IdeaResult:
    result = IdeaResult(provider=provider_name, idea=idea)
    inner = (factory or _provider_factory(provider_name))(idea)
    provider = InstrumentedProvider(inner)
    if guard is not None:
        guard.start_idea()

    test_seconds = 0.0
    test_runs = 0
    original = qa_runner.run_generated_tests

    def timed_runner(backend_dir: Path, timeout_s: float = qa_runner.DEFAULT_TEST_TIMEOUT_S) -> qa_runner.TestRunResult:
        nonlocal test_seconds, test_runs
        t0 = time.perf_counter()
        try:
            return original(backend_dir, timeout_s)
        finally:
            test_seconds += time.perf_counter() - t0
            test_runs += 1

    qa_runner.run_generated_tests = timed_runner  # type: ignore[assignment]
    t0 = time.perf_counter()
    team = NexusITTeam(provider=provider) if squad_budget_usd is None else NexusITTeam(provider, squad_budget_usd)
    try:
        project = team.build_from_idea(idea, output_dir=workdir, max_healing_cycles=max_healing_cycles)
    except SpendCapReached:
        raise
    except Exception as exc:  # noqa: BLE001 - a benchmark records failures instead of stopping
        cause = exc.__cause__ or exc.__context__
        if isinstance(cause, SpendCapReached):
            raise cause from exc
        result.error = f"{type(exc).__name__}: {exc}"[:300]
        return result
    finally:
        qa_runner.run_generated_tests = original  # type: ignore[assignment]
        if guard is not None:
            result.spend_usd = round(guard.idea_spent_usd(), 6)
        result.total_seconds = time.perf_counter() - t0
        result.test_run_seconds = test_seconds
        result.test_runs = test_runs
        result.stages = {k: asdict(v) for k, v in provider.stages.items()}
        result.generation_seconds = sum(v.seconds for v in provider.stages.values())

    app_dir = (
        Path(project.output_path) if project.output_path else workdir / tpl.service_slug(project.proposal.app_name)
    )
    backend = app_dir / "backend"
    result.app_dir = str(app_dir)
    result.qa_gate = project.qa_passed
    result.healing_cycles = project.healing_report.total_cycles if project.healing_report else 0
    if project.test_run is not None:
        result.tests_pass = project.test_run.passed
        result.tests_passed = project.test_run.tests_passed
        result.tests_failed = project.test_run.tests_failed + project.test_run.tests_errored
    result.compile_errors = check_builds(backend) if backend.is_dir() else ["no backend/ directory"]
    result.builds = not result.compile_errors
    if result.builds:
        result.starts, result.start_seconds = check_starts(backend)
    result.end_to_end = result.builds and result.starts and result.tests_pass
    return result


def _pct(n: int, d: int) -> str:
    return f"{n}/{d} ({100.0 * n / d:.0f}%)" if d else "0/0"


def summarize(results: list[IdeaResult]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    by_provider: dict[str, list[IdeaResult]] = defaultdict(list)
    for r in results:
        by_provider[r.provider].append(r)
    for name, rs in by_provider.items():
        n = len(rs)
        stage_totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for r in rs:
            for stage, st in r.stages.items():
                for k, v in st.items():
                    stage_totals[stage][k] += v
        out[name] = {
            "ideas": n,
            "builds": sum(r.builds for r in rs),
            "starts": sum(r.starts for r in rs),
            "tests_pass": sum(r.tests_pass for r in rs),
            "qa_gate": sum(r.qa_gate for r in rs),
            "end_to_end": sum(r.end_to_end for r in rs),
            "errors": [r.error for r in rs if r.error],
            "spend_usd": round(sum(r.spend_usd for r in rs), 4),
            "median_total_s": statistics.median(r.total_seconds for r in rs),
            "median_generation_s": statistics.median(r.generation_seconds for r in rs),
            "median_test_run_s": statistics.median(r.test_run_seconds for r in rs),
            "median_test_runs": statistics.median(r.test_runs for r in rs),
            "median_start_s": statistics.median([r.start_seconds for r in rs if r.start_seconds] or [0.0]),
            "median_healing_cycles": statistics.median(r.healing_cycles for r in rs),
            "per_run_stage_avg": {
                stage: {k: round(v / n, 4) for k, v in vals.items()} for stage, vals in stage_totals.items()
            },
        }
    return out


def print_report(summary: dict[str, Any]) -> None:
    for name, s in summary.items():
        n = s["ideas"]
        print(f"\n== provider: {name} ({n} ideas)")
        print(f"  builds        {_pct(s['builds'], n)}")
        print(f"  starts        {_pct(s['starts'], n)}")
        print(f"  tests pass    {_pct(s['tests_pass'], n)}")
        print(f"  QA gate       {_pct(s['qa_gate'], n)}")
        print(f"  END TO END    {_pct(s['end_to_end'], n)}")
        if s["spend_usd"]:
            print(f"  model spend   {s['spend_usd']:.4f} USD (benchmark prices)")
        print(
            f"  median: total {s['median_total_s']:.2f}s, generation {s['median_generation_s']:.3f}s, "
            f"test runs {s['median_test_runs']} taking {s['median_test_run_s']:.2f}s, "
            f"start {s['median_start_s']:.2f}s, healing cycles {s['median_healing_cycles']}"
        )
        print("  per run, by stage: calls | prompt chars (~tokens) | output chars (~tokens) | reported in/out tokens")
        tot_p = tot_o = 0.0
        for stage, st in sorted(s["per_run_stage_avg"].items()):
            tot_p += st["prompt_chars"]
            tot_o += st["output_chars"]
            print(
                f"    {stage:<24} {st['calls']:>4.1f} | {st['prompt_chars']:>8.0f} (~{st['prompt_chars'] / 4:>6.0f}) | "
                f"{st['output_chars']:>8.0f} (~{st['output_chars'] / 4:>6.0f}) | "
                f"{st['input_tokens']:.0f}/{st['output_tokens']:.0f}"
            )
        print(f"    {'TOTAL':<24}      | {tot_p:>8.0f} (~{tot_p / 4:>6.0f}) | {tot_o:>8.0f} (~{tot_o / 4:>6.0f}) |")
        for err in s["errors"]:
            print(f"  error: {err}")


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--providers", nargs="+", default=["deterministic", "mock"])
    ap.add_argument("--ideas", type=int, default=len(IDEAS), help="use the first N ideas of the fixed set")
    ap.add_argument("--from-idea", type=int, default=0, help="skip the first N ideas (resume a stopped run)")
    ap.add_argument("--max-healing-cycles", type=int, default=3)
    ap.add_argument("--json", type=Path, help="write raw results and summary to this file")
    ap.add_argument("--keep", action="store_true", help="keep the generated workspaces")
    ap.add_argument("--project", default=os.getenv("GCP_PROJECT_ID"), help="Google Cloud project (vertex)")
    ap.add_argument("--model", default=None, help="model id for vertex (default gemini-3.8-flash)")
    ap.add_argument("--max-spend-usd", type=float, default=5.0, help="vertex: stop the whole run here")
    ap.add_argument("--per-idea-spend-usd", type=float, default=1.5, help="vertex: stop one idea here")
    ap.add_argument("--price-in", type=float, default=1.0, help="vertex: USD per million input tokens")
    ap.add_argument("--price-out", type=float, default=5.0, help="vertex: USD per million output tokens")
    args = ap.parse_args(argv)

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    guard = SpendGuard(args.max_spend_usd, args.per_idea_spend_usd, args.price_in, args.price_out)
    results: list[IdeaResult] = []
    tmp_root = Path(tempfile.mkdtemp(prefix="nexus_bench_"))
    stopped = False
    try:
        for provider_name in args.providers:
            paid = provider_name == "vertex"
            factory = _provider_factory(provider_name, args.project, args.model, guard if paid else None)
            for i, idea in list(enumerate(IDEAS[: args.ideas]))[args.from_idea :]:
                workdir = tmp_root / provider_name / f"idea{i}"
                workdir.mkdir(parents=True)
                try:
                    r = run_one(provider_name, idea, workdir, args.max_healing_cycles, factory, guard if paid else None)
                except SpendCapReached as exc:
                    r = IdeaResult(provider=provider_name, idea=idea, error=f"SpendCapReached: {exc}")
                    r.spend_usd = round(guard.idea_spent_usd(), 6)
                    stopped = "run spend cap" in str(exc)
                flag = "PASS" if r.end_to_end else "FAIL"
                print(
                    f"[{provider_name}] {flag} build={r.builds} start={r.starts} tests={r.tests_pass} "
                    f"heal={r.healing_cycles} {r.total_seconds:.1f}s"
                    + (f" ${r.spend_usd:.3f} (run ${guard.spent_usd:.3f})" if paid else "")
                    + f"  {idea[:50]}"
                    + (f"  ERROR {r.error}" if r.error else "")
                    + (f"  compile: {r.compile_errors[:2]}" if r.compile_errors else ""),
                    flush=True,
                )
                results.append(r)
                if stopped:
                    break
            if stopped:
                break
    finally:
        if not args.keep:
            import shutil

            shutil.rmtree(tmp_root, ignore_errors=True)
        else:
            print(f"workspaces kept in {tmp_root}")

    summary = summarize(results)
    print_report(summary)
    usage = {
        "calls": guard.calls,
        "input_tokens": guard.input_tokens,
        "output_tokens": guard.output_tokens,
        "thinking_tokens": guard.thinking_tokens,
        "token_refreshes": guard.token_refreshes,
        "spend_usd": round(guard.spent_usd, 4),
        "price_in_per_m": guard.price_in_per_m,
        "price_out_per_m": guard.price_out_per_m,
    }
    if guard.calls:
        print(
            f"\npaid model usage: {guard.calls} calls, {guard.input_tokens} in, {guard.output_tokens} out, "
            f"{guard.thinking_tokens} thinking tokens = {guard.spent_usd:.4f} USD at "
            f"{guard.price_in_per_m}/{guard.price_out_per_m} USD per million"
        )
    if args.json:
        args.json.write_text(
            json.dumps({"summary": summary, "usage": usage, "results": [asdict(r) for r in results]}, indent=2),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
