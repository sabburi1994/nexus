"""Generated workspace: package names, Dockerfile, Terraform, deploy script, real QA and spend cap."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from nexus import __version__
from nexus.agents.context import BudgetExceededError
from nexus.maintenance.healer import DiagnosisResult
from nexus.providers.base import ProviderUsage
from nexus.providers.mock import MockProvider
from nexus.qa.runner import run_generated_tests
from nexus.teams.it_pack import platform_templates as tpl
from nexus.teams.it_pack.ba import ProductProposal
from nexus.teams.it_pack.data_architect import DataArchitecture
from nexus.teams.it_pack.designer import UiSpecification
from nexus.teams.it_pack.devops import DevopsSpecification
from nexus.teams.it_pack.fullstack import FullStackSpecification
from nexus.teams.it_pack.qa import QaSpecification
from nexus.teams.it_pack.solution_architect import SolutionBlueprint
from nexus.teams.it_pack.team import DeliveredProject, NexusITTeam

HEALTHY_MAIN = """from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "healthy": True}
"""

BROKEN_MAIN = """from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "down", "healthy": False}
"""

HEALTH_TEST = """from fastapi.testclient import TestClient

from main import app


def test_health() -> None:
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
"""


def _fullstack(main_py: str) -> FullStackSpecification:
    return FullStackSpecification(
        backend_main_py=main_py,
        backend_models_py="from pydantic import BaseModel\n\n\nclass Item(BaseModel):\n    name: str\n",
        frontend_app_tsx="export default function App() { return <div>App</div>; }",
        frontend_api_client_ts="export async function getItems() { return []; }",
    )


def _qa(test_code: str, passed: bool = True) -> QaSpecification:
    return QaSpecification(test_suite_code=test_code, security_verdict="reviewed", passed_preflight=passed)


class ScriptedProvider(MockProvider):
    """Returns queued responses per schema (the last one repeats) and records every prompt."""

    def __init__(self, responses: dict[type[BaseModel], list[Any]], cost_per_call: float = 0.0) -> None:
        super().__init__()
        self.responses = {k: list(v) for k, v in responses.items()}
        self.cost_per_call = cost_per_call
        self.prompts: list[tuple[str, str]] = []

    def structured(self, prompt: str, response_model: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        self.prompts.append((response_model.__name__, prompt))
        self.last_usage = ProviderUsage(10, 10, self.cost_per_call, "scripted")
        queue = self.responses.get(response_model)
        if queue:
            return queue.pop(0) if len(queue) > 1 else queue[0]
        return super().structured(prompt, response_model, **kwargs)


def _squad_responses(
    fullstack: list[FullStackSpecification],
    qa: list[QaSpecification],
    devops: DevopsSpecification | None = None,
) -> dict[type[BaseModel], list[Any]]:
    return {
        ProductProposal: [
            ProductProposal(
                app_name="WatchHub",
                title="WatchHub",
                tagline="Watch tracker",
                target_audience="Collectors",
                user_stories=["As a user, I want price alerts"],
                core_features=["Price alerts"],
                ui_concept="Dashboard",
                wireframe_preview_html="<div>Mockup</div>",
            )
        ],
        SolutionBlueprint: [
            SolutionBlueprint(
                cloud_provider="gcp",
                compute_pattern="Cloud Run",
                system_topology="React -> Cloud Run",
                non_functional_requirements=["Scale to zero"],
                integration_services=["Secret Manager"],
            )
        ],
        DataArchitecture: [
            DataArchitecture(
                database_engine="PostgreSQL 16",
                tables=["watches"],
                relationships=[],
                indexes=[],
                sql_ddl_schema="CREATE TABLE watches (id UUID PRIMARY KEY);",
            )
        ],
        UiSpecification: [UiSpecification(component_name="WatchDashboard", color_palette="slate", react_code="x")],
        FullStackSpecification: list(fullstack),
        DevopsSpecification: [
            devops
            or DevopsSpecification(
                cloud_target="gcp",
                docker_compose_yml="services: {}",
                needs_vertex_ai=False,
                runtime_secrets=["DATABASE_PASSWORD"],
                # A model that ignores the instructions: these must be overwritten by the templates.
                terraform_main_tf='resource "google_cloud_run_v2_service" "x" { max_instance_count = 5 }',
                deploy_script_sh="name: Deploy\non: [push]",
            )
        ],
        QaSpecification: list(qa),
        DiagnosisResult: [
            DiagnosisResult(
                root_cause="health returns down", suggested_fix="return ok", is_transient=False, confidence=0.9
            )
        ],
    }


def _build(tmp_path: Path, provider: ScriptedProvider, **team_kwargs: Any) -> DeliveredProject:
    team = NexusITTeam(provider=provider, **team_kwargs)
    return team.build_from_idea("A watch tracker", output_dir=tmp_path, max_healing_cycles=2)


@pytest.fixture
def healthy_project(tmp_path: Path) -> tuple[DeliveredProject, Path]:
    provider = ScriptedProvider(_squad_responses([_fullstack(HEALTHY_MAIN)], [_qa(HEALTH_TEST)]))
    project = _build(tmp_path, provider)
    assert project.output_path is not None
    return project, Path(project.output_path)


# 1 and 2: package names


def test_generated_backend_depends_on_published_framework_package(
    healthy_project: tuple[DeliveredProject, Path],
) -> None:
    _, app = healthy_project
    pyproject = (app / "backend" / "pyproject.toml").read_text(encoding="utf-8")
    requirements = (app / "backend" / "requirements.txt").read_text(encoding="utf-8")
    assert f'"nexus-agent-framework>={__version__}"' in pyproject
    assert f"nexus-agent-framework>={__version__}" in requirements
    assert '"nexus-framework' not in pyproject and "nexus-framework>" not in requirements


def test_generated_frontend_uses_published_npm_packages(healthy_project: tuple[DeliveredProject, Path]) -> None:
    _, app = healthy_project
    pkg = json.loads((app / "frontend" / "package.json").read_text(encoding="utf-8"))
    deps = pkg["dependencies"]
    assert deps["@nexus-agent-framework/ui"] == "^0.2.0"
    assert deps["@nexus-agent-framework/contracts"] == "^1.0.4"
    assert not any(name.startswith("@nexus/") for name in deps)
    assert "workspace:" not in json.dumps(pkg)


def test_npm_ranges_match_the_packages_in_this_repo() -> None:
    root = Path(__file__).resolve().parent.parent / "packages"
    ui = json.loads((root / "ui" / "package.json").read_text(encoding="utf-8"))
    contracts = json.loads((root / "contracts" / "package.json").read_text(encoding="utf-8"))
    # UI: generated apps stay on the 0.2 line (their templates use components 1.x moved to /showcase).
    assert ui["name"] == tpl.UI_PACKAGE and tpl.UI_VERSION_RANGE == f"^{tpl.UI_PUBLISHED_VERSION}"
    published = tuple(int(x) for x in tpl.UI_PUBLISHED_VERSION.split("."))
    assert tuple(int(x) for x in ui["version"].split(".")) >= published
    assert contracts["name"] == tpl.CONTRACTS_PACKAGE and tpl.CONTRACTS_VERSION_RANGE == f"^{contracts['version']}"


# 3: Dockerfile


def test_generated_dockerfile_runs_as_non_root_on_8080(healthy_project: tuple[DeliveredProject, Path]) -> None:
    project, app = healthy_project
    dockerfile = (app / "backend" / "Dockerfile").read_text(encoding="utf-8")
    assert dockerfile == project.devops.dockerfile == tpl.render_dockerfile()
    lines = [ln.strip() for ln in dockerfile.splitlines()]
    user_lines = [ln for ln in lines if ln.startswith("USER ")]
    assert user_lines == ["USER 10001:10001"]
    # USER comes before CMD, so the server never runs as root.
    assert lines.index(user_lines[0]) < next(i for i, ln in enumerate(lines) if ln.startswith("CMD "))
    assert "EXPOSE 8080" in lines
    assert '"--port", "8080"' in dockerfile
    assert "requirements.txt" in dockerfile
    assert "tests/" in (app / "backend" / ".dockerignore").read_text(encoding="utf-8")


# 4: Terraform from the platform modules


def test_generated_terraform_uses_platform_modules(healthy_project: tuple[DeliveredProject, Path]) -> None:
    _, app = healthy_project
    main_tf = (app / "infra" / "terraform" / "main.tf").read_text(encoding="utf-8")
    variables_tf = (app / "infra" / "terraform" / "variables.tf").read_text(encoding="utf-8")

    assert f"modules/nexus_app?ref=v{__version__}" in main_tf
    assert f"modules/nexus_cloud_run?ref=v{__version__}" in main_tf
    assert "min_instances         = 0" in main_tf
    assert "max_instances         = 2" in main_tf
    assert "cpu_idle              = true" in main_tf
    assert "image_tag             = var.image_tag" in main_tf
    # The model's own Terraform (max 5 instances) was replaced.
    assert "max_instance_count = 5" not in main_tf
    # No Vertex AI grant when the app does not call it; secrets granted per secret only.
    assert "enable_ai          = false" in main_tf
    assert "aiplatform" not in main_tf
    assert "secretAccessor" not in main_tf
    assert 'env_name = "DATABASE_PASSWORD"' in main_tf
    assert '"watchhub-database-password"' in main_tf
    # image_tag is required: no default, "latest" rejected.
    image_tag_block = variables_tf[variables_tf.index('variable "image_tag"') :]
    assert "default" not in image_tag_block
    assert 'var.image_tag != "latest"' in image_tag_block


def test_vertex_ai_enabled_only_when_needed() -> None:
    assert "enable_ai          = true" in tpl.render_terraform_main("app", needs_vertex_ai=True, runtime_secrets=[])
    no_ai = tpl.render_terraform_main("app", needs_vertex_ai=False, runtime_secrets=[])
    assert "enable_ai          = false" in no_ai
    assert "google_secret_manager_secret" not in no_ai


def test_model_supplied_names_are_sanitized() -> None:
    assert tpl.service_slug("../../etc/passwd") == "etc-passwd"
    assert tpl.service_slug("123 Go") == "app-123-go"
    assert tpl.service_slug("") == "nexus-app"
    assert len(tpl.service_slug("x" * 200)) <= 40
    account = tpl.runtime_account_id("a")
    assert 6 <= len(account) <= 30 and account[0].isalpha()
    assert len(tpl.runtime_account_id("y" * 200)) <= 30
    assert tpl.runtime_secret_env_names(["db password", "API_KEY", "api_key", "1bad", '"; rm -rf']) == [
        "DB_PASSWORD",
        "API_KEY",
        "RM_RF",
    ]


# 5: deploy script path


def test_deploy_script_written_to_scripts_not_github_workflows(healthy_project: tuple[DeliveredProject, Path]) -> None:
    _, app = healthy_project
    script = app / "scripts" / "deploy.sh"
    assert script.is_file()
    assert not (app / ".github").exists()
    raw = script.read_bytes()
    assert raw.startswith(b"#!/usr/bin/env bash\n")
    assert b"\r\n" not in raw
    text = raw.decode("utf-8")
    assert "git rev-parse --short=12 HEAD" in text
    assert "image_tag=${TAG}" in text
    assert "name: Deploy" not in text


def _find_working_bash() -> str | None:
    """Return a working bash binary, ignoring an unconfigured Windows WSL shim."""
    candidates: list[str] = []
    which_bash = shutil.which("bash")
    if which_bash:
        candidates.append(which_bash)
    for fallback in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"):
        if Path(fallback).is_file() and fallback not in candidates:
            candidates.append(fallback)
    for candidate in candidates:
        probe = subprocess.run([candidate, "-c", "true"], capture_output=True, check=False)
        if probe.returncode == 0:
            return candidate
    return None


_WORKING_BASH = _find_working_bash()


@pytest.mark.skipif(_WORKING_BASH is None, reason="working bash not installed")
def test_deploy_script_is_valid_bash(tmp_path: Path) -> None:
    assert _WORKING_BASH is not None
    script = tmp_path / "deploy.sh"
    script.write_text(tpl.render_deploy_script("WatchHub"), encoding="utf-8", newline="\n")
    proc = subprocess.run([_WORKING_BASH, "-n", str(script)], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr


# 6: real test execution


def test_generated_suite_is_executed_for_real(healthy_project: tuple[DeliveredProject, Path]) -> None:
    project, _ = healthy_project
    assert project.test_run is not None
    assert project.test_run.executed and project.test_run.passed
    assert project.test_run.tests_passed == 1
    assert project.qa_passed is True
    assert project.healing_report is None


def test_real_failure_triggers_healing_even_when_qa_self_reports_pass(tmp_path: Path) -> None:
    provider = ScriptedProvider(
        _squad_responses(
            fullstack=[_fullstack(BROKEN_MAIN), _fullstack(HEALTHY_MAIN)],
            # QA claims the broken code passes; only the real run can tell.
            qa=[_qa(HEALTH_TEST, passed=True)],
        )
    )
    project = _build(tmp_path, provider)

    report = project.healing_report
    assert report is not None
    assert report.was_healing_required and report.tests_executed
    assert report.initial_test_run is not None and not report.initial_test_run.passed
    assert report.initial_test_run.tests_failed == 1
    assert report.resolved and report.total_cycles == 1
    assert report.attempts[0].test_run is not None and report.attempts[0].test_run.passed
    assert project.test_run is not None and project.test_run.passed
    assert project.qa_passed

    # The diagnosis saw the actual pytest failure, not just QA's verdict.
    diagnosis_prompts = [p for name, p in provider.prompts if name == "DiagnosisResult"]
    assert len(diagnosis_prompts) == 1
    assert "Generated pytest suite failed" in diagnosis_prompts[0]
    assert "'down' == 'ok'" in diagnosis_prompts[0] or "AssertionError" in diagnosis_prompts[0]

    # The healed code is what ends up on disk.
    assert "ok" in (Path(project.output_path or "") / "backend" / "src" / "main.py").read_text(encoding="utf-8")


def test_unresolved_real_failure_fails_the_gate(tmp_path: Path) -> None:
    provider = ScriptedProvider(_squad_responses([_fullstack(BROKEN_MAIN)], [_qa(HEALTH_TEST, passed=True)]))
    project = _build(tmp_path, provider)
    assert project.healing_report is not None
    assert project.healing_report.final_verdict == "FAIL_MAX_CYCLES_EXCEEDED"
    assert project.healing_report.total_cycles == 2
    assert project.qa_passed is False
    assert project.qa.passed_preflight is True  # the self report alone would have passed it


def test_test_execution_can_be_disabled(tmp_path: Path) -> None:
    provider = ScriptedProvider(_squad_responses([_fullstack(BROKEN_MAIN)], [_qa(HEALTH_TEST, passed=True)]))
    project = _build(tmp_path, provider, run_generated_tests=False)
    assert project.test_run is None
    assert project.healing_report is None
    assert project.qa_passed is True  # self reported only


def test_no_output_dir_keeps_self_reported_gate() -> None:
    provider = ScriptedProvider(_squad_responses([_fullstack(BROKEN_MAIN)], [_qa(HEALTH_TEST, passed=True)]))
    project = NexusITTeam(provider=provider).build_from_idea("A watch tracker")
    assert project.output_path is None and project.test_run is None


def test_mock_provider_run_with_workspace_completes(tmp_path: Path) -> None:
    project = NexusITTeam(provider=MockProvider()).build_from_idea(
        "Telemetry platform", output_dir=tmp_path, max_healing_cycles=1
    )
    # MockProvider's placeholder code cannot pass a real run; the loop is bounded and reports it.
    assert project.test_run is not None and project.test_run.executed and not project.test_run.passed
    assert project.healing_report is not None and project.healing_report.total_cycles == 1
    assert project.qa_passed is False
    assert project.cost_usd == 0.0


def _write_suite(backend: Path, test_code: str) -> None:
    (backend / "src").mkdir(parents=True)
    (backend / "tests").mkdir()
    (backend / "tests" / "test_x.py").write_text(test_code, encoding="utf-8")


def test_runner_times_out(tmp_path: Path) -> None:
    _write_suite(tmp_path, "import time\n\n\ndef test_slow() -> None:\n    time.sleep(30)\n")
    result = run_generated_tests(tmp_path, timeout_s=3)
    assert result.executed and result.timed_out and not result.passed
    assert "timed out" in result.summary


def test_runner_hides_parent_secrets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXUS_FAKE_SECRET_FOR_TEST", "do-not-leak")
    _write_suite(
        tmp_path,
        "import os\n\n\ndef test_env() -> None:\n    assert 'NEXUS_FAKE_SECRET_FOR_TEST' not in os.environ\n",
    )
    result = run_generated_tests(tmp_path, timeout_s=60)
    assert result.passed, result.output_tail


def test_runner_reports_empty_suite_as_failure(tmp_path: Path) -> None:
    _write_suite(tmp_path, "# no tests\n")
    result = run_generated_tests(tmp_path, timeout_s=60)
    assert result.executed and not result.passed and result.exit_code == 5


# 7: spend cap


def test_squad_run_stops_at_budget(tmp_path: Path) -> None:
    provider = ScriptedProvider(
        _squad_responses([_fullstack(HEALTHY_MAIN)], [_qa(HEALTH_TEST)]),
        cost_per_call=0.30,
    )
    team = NexusITTeam(provider=provider, max_budget_usd=1.00)
    with pytest.raises(BudgetExceededError):
        team.build_from_idea("A watch tracker", output_dir=tmp_path)
    # Four calls cost $1.20: the run stopped right after the call that crossed the cap.
    assert len(provider.prompts) == 4
    assert team.context.accumulated_cost_usd == pytest.approx(1.20)


def test_squad_run_reports_spend_within_budget(healthy_project: tuple[DeliveredProject, Path]) -> None:
    project, _ = healthy_project
    assert project.cost_usd == 0.0
    assert project.budget_usd == 1.00


def test_budget_resets_per_run() -> None:
    provider = ScriptedProvider(_squad_responses([_fullstack(HEALTHY_MAIN)], [_qa(HEALTH_TEST)]), cost_per_call=0.05)
    team = NexusITTeam(provider=provider, max_budget_usd=0.50)
    first = team.build_from_idea("A watch tracker")
    second = team.build_from_idea("A watch tracker")
    assert first.cost_usd == pytest.approx(second.cost_usd)
    assert first.cost_usd == pytest.approx(0.05 * 7)


def test_devops_spec_accepts_the_old_deploy_field_name() -> None:
    spec = DevopsSpecification.model_validate(
        {"cloud_target": "gcp", "docker_compose_yml": "", "ci_cd_workflow_yml": "#!/usr/bin/env bash"}
    )
    assert spec.deploy_script_sh == spec.ci_cd_workflow_yml == "#!/usr/bin/env bash"
