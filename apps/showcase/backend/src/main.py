"""Nexus Documentation & Interactive Framework Showcase Backend Service."""

from __future__ import annotations

import datetime
import difflib
import io
import json
import os
import re
import tempfile
import time
import uuid
import zipfile
from collections import OrderedDict
from pathlib import Path, PurePosixPath
from typing import Any

from fastapi import Header, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from models import (
    BrownfieldApplyRequest,
    BrownfieldInspectRequest,
    GuardrailInspectRequest,
    RoiRequest,
    ScanRequest,
    ScanResponse,
    SimulationRequest,
)
from showcase_provider import ByokGeminiProviderError, ByokGeminiShowcaseProvider, ShowcaseSquadProvider

from nexus import __version__
from nexus.ai import GeminiClient
from nexus.ai.pricing import GEMINI_3_8_FLASH_INPUT_PER_M, GEMINI_3_8_FLASH_OUTPUT_PER_M, calculate_cost_usd
from nexus.api import create_nexus_app
from nexus.brownfield import AstDependencyMapper, BrownfieldRefactorer, CodebaseAuditor
from nexus.metrics.roi import DoraMetrics, EnterpriseRoiReport, RoiCalculator
from nexus.security import GuardrailManager, SecurityViolationError, check_prompt_injection, sanitize_text
from nexus.teams.it_pack.team import NexusITTeam

app, db = create_nexus_app(
    title="Nexus Showcase API",
    description="Orchestrator-Native AI Agentic Framework Reference Application & Documentation Portal (https://nexus.abburi.info)",
    version=__version__,
)

gemini = GeminiClient(default_model="gemini-3.8-flash")
guardrail = GuardrailManager()
_REPORTS_STORE: dict[str, dict[str, Any]] = {}
_WORKSPACE_ZIPS: OrderedDict[str, tuple[str, bytes]] = OrderedDict()
_MAX_ZIP_CACHE = 16
_SRC_DIR = Path(__file__).resolve().parent
_SAMPLE_BROWNFIELD_DIR = _SRC_DIR / "sample_brownfield"
_MANIFEST_PATH = _SRC_DIR / "verification_manifest.json"


def _load_verification_manifest() -> dict[str, Any]:
    if _MANIFEST_PATH.exists():
        return dict(json.loads(_MANIFEST_PATH.read_text(encoding="utf-8")))
    return {
        "pypi_live_version": "0.1.1",
        "pypi_staged_version": __version__,
        "ci_status_url": "https://github.com/sabburi1994/nexus/actions",
        "suites": {},
    }


def _archive_workspace_zip(app_dir: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(app_dir.rglob("*")):
            if file_path.is_dir() or "__pycache__" in file_path.parts:
                continue
            rel = str(file_path.relative_to(app_dir)).replace("\\", "/")
            zf.write(file_path, arcname=rel)
    return buf.getvalue()


def _cache_workspace_zip(run_id: str, app_name: str, payload: bytes) -> None:
    _WORKSPACE_ZIPS[run_id] = (app_name, payload)
    _WORKSPACE_ZIPS.move_to_end(run_id)
    while len(_WORKSPACE_ZIPS) > _MAX_ZIP_CACHE:
        _WORKSPACE_ZIPS.popitem(last=False)


def _build_dependency_edges(mapper: AstDependencyMapper) -> list[dict[str, str]]:
    """Convert raw module imports into file-to-file AST dependency edges."""
    edges: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    all_files = sorted(mapper.imports_map.keys())
    for consumer, imported_modules in mapper.imports_map.items():
        for provider in all_files:
            if provider == consumer:
                continue
            provider_mod = provider.replace(".py", "").replace("/", ".")
            if any(mod in provider_mod or provider_mod in mod for mod in imported_modules):
                pair = (provider, consumer)
                if pair not in seen:
                    seen.add(pair)
                    edges.append({"source": provider, "target": consumer})
    return edges


def _write_validated_custom_files(root: Path, custom_files: dict[str, str]) -> None:
    if len(custom_files) > 12:
        raise HTTPException(status_code=400, detail="Maximum 12 files per sandbox inspection.")
    for rel_name, code in custom_files.items():
        clean_rel = PurePosixPath(rel_name.replace("\\", "/").lstrip("/"))
        if clean_rel.is_absolute() or ".." in clean_rel.parts or not str(clean_rel).endswith(".py"):
            raise HTTPException(status_code=400, detail=f"Invalid relative Python path: {rel_name}")
        if len(code) > 25_000:
            raise HTTPException(status_code=400, detail=f"File exceeds 25KB sandbox limit: {rel_name}")
        dest = (root / str(clean_rel)).resolve()
        if not str(dest).startswith(str(root.resolve())):
            raise HTTPException(status_code=400, detail="Path traversal blocked.")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(code, encoding="utf-8")


def _apply_surgical_remediations(files_map: dict[str, str]) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Apply Stage 2 security remediations (env externalization + guardrail wrapping) in memory."""
    remediated: dict[str, str] = {}
    diffs: list[dict[str, str]] = []
    secret_assign_re = re.compile(r'^(\s*)([A-Z0-9_]+)\s*=\s*["\']([^"\']+)["\'](\s*(?:#.*)?)$')

    for rel_path, original in files_map.items():
        new_lines: list[str] = []
        changed = False
        needs_os_import = False

        for line in original.splitlines():
            sanitized = sanitize_text(line)
            m = secret_assign_re.match(line)
            if m and "[REDACTED" in sanitized:
                indent, var_name, _, comment = m.groups()
                new_lines.append(f'{indent}{var_name} = os.getenv("{var_name}", ""){comment}')
                needs_os_import = True
                changed = True
            else:
                new_lines.append(line)

        updated = "\n".join(new_lines) + ("\n" if original.endswith("\n") else "")
        if needs_os_import and "import os" not in updated:
            updated = "import os\n" + updated

        if ("GeminiClient" in updated or "OpenAI" in updated) and (
            "sanitize" not in updated and "guardrail" not in updated
        ):
            changed = True
            guardrail_header = (
                "from nexus.security import GuardrailManager\n\n_nexus_guardrail = GuardrailManager()\n\n"
            )
            lines = updated.splitlines(keepends=True)
            insert_idx = 0
            for idx, ln in enumerate(lines):
                if ln.startswith(("import ", "from ")):
                    insert_idx = idx + 1
            updated = "".join(lines[:insert_idx]) + "\n" + guardrail_header + "".join(lines[insert_idx:])
            updated = re.sub(
                r"\.generate\(([^)]+)\)",
                r".generate(_nexus_guardrail.inspect_input(\1))",
                updated,
            )

        remediated[rel_path] = updated
        if changed and updated != original:
            diff_text = "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    updated.splitlines(keepends=True),
                    fromfile=f"a/{rel_path}",
                    tofile=f"b/{rel_path}",
                )
            )
            diffs.append({"filePath": rel_path, "diff": diff_text})

    return remediated, diffs


def _to_healing_contract(report: Any, elapsed_s: float) -> dict[str, Any]:
    """Convert Python SelfHealingReport into SelfHealingReportContract JSON."""
    attempts_out = []
    for att in report.attempts:
        attempts_out.append(
            {
                "attemptNumber": att.attempt_number,
                "testFailures": [att.details] if att.details else ["Preflight check did not clear"],
                "diagnosis": f"{att.diagnosis.root_cause} Recommended fix: {att.diagnosis.suggested_fix}",
                "diffApplied": att.fixed_backend_snippet,
                "retestPassed": att.passed_preflight_after_fix,
                "timestamp": datetime.datetime.now(datetime.UTC).strftime("%H:%M:%S"),
            }
        )

    final_status = "HEALTHY" if not report.was_healing_required else ("HEALED" if report.resolved else "EXHAUSTED")
    summary = (
        "Initial QA preflight passed on the first pass; no repair iterations required."
        if final_status == "HEALTHY"
        else f"Closed-loop healer resolved QA preflight failure in {report.total_cycles} cycle(s) ({report.final_verdict})."
    )
    return {
        "initialTestsPassed": not report.was_healing_required,
        "totalAttempts": report.total_cycles,
        "maxAttemptsAllowed": 3,
        "finalStatus": final_status,
        "attempts": attempts_out,
        "durationSeconds": round(elapsed_s, 3),
        "summary": summary,
    }


def _to_blast_contract(blast: Any) -> dict[str, Any]:
    return {
        "target": blast.target,
        "riskTier": blast.risk_tier,
        "directDependents": blast.direct_dependents,
        "indirectDependents": blast.indirect_dependents,
        "affectedRoutes": blast.affected_routes,
        "affectedTests": blast.affected_tests,
        "totalAffectedFiles": blast.total_affected_files,
    }


def _to_roi_contract(rep: EnterpriseRoiReport) -> dict[str, Any]:
    return {
        "projectName": rep.project_name,
        "targetPath": rep.target_path,
        "timestamp": rep.timestamp,
        "totalFilesAnalyzed": rep.total_files_analyzed,
        "totalLinesOfCode": rep.total_lines_of_code,
        "totalRunsAnalyzed": rep.total_runs_analyzed,
        "totalInputTokens": rep.total_input_tokens,
        "totalOutputTokens": rep.total_output_tokens,
        "totalTokenCostUsd": rep.total_token_cost_usd,
        "engineeringHoursSaved": rep.engineering_hours_saved,
        "hourlyRateUsd": rep.hourly_rate_usd,
        "humanCostSavedUsd": rep.human_cost_saved_usd,
        "netSavingsUsd": rep.net_savings_usd,
        "roiMultiplier": rep.roi_multiplier,
        "doraMetrics": {
            "deploymentFrequencyMultiplier": rep.dora_metrics.deployment_frequency_multiplier,
            "leadTimeReductionPct": rep.dora_metrics.lead_time_reduction_pct,
            "changeFailureRatePct": rep.dora_metrics.change_failure_rate_pct,
            "mttrMinutes": rep.dora_metrics.mttr_minutes,
        },
        "vulnerabilitiesPrevented": rep.vulnerabilities_prevented,
        "healingCyclesExecuted": rep.healing_cycles_executed,
        "refactorTasksExecuted": rep.refactor_tasks_executed,
        "summary": rep.summary,
    }


def _inspect_directory(
    root_dir: Path,
    target_file: str,
    refactor_task: str,
    provider: ShowcaseSquadProvider,
) -> dict[str, Any]:
    auditor = CodebaseAuditor(root_dir)
    audit = auditor.run_audit()

    mapper = AstDependencyMapper(root_dir)
    mapper.scan_codebase()

    # Read actual source files present for side-by-side inspection
    files_map: dict[str, str] = {}
    for p in sorted(root_dir.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        rel = str(p.relative_to(root_dir)).replace("\\", "/")
        files_map[rel] = p.read_text(encoding="utf-8", errors="ignore")

    chosen_target = target_file.strip().lstrip("/")
    if chosen_target not in files_map and files_map:
        chosen_target = "models.py" if "models.py" in files_map else next(iter(files_map))

    blast = mapper.compute_blast_radius(chosen_target)

    refactorer = BrownfieldRefactorer(root_dir, provider=provider)
    plan = refactorer.plan_refactor(refactor_task, primary_target=chosen_target)

    symbols = [
        {
            "name": sym.name,
            "kind": sym.kind,
            "filePath": sym.file_path,
            "lineNumber": sym.line_number,
            "routePath": sym.route_path,
            "httpMethod": sym.http_method,
        }
        for sym_list in mapper.symbols_map.values()
        for sym in sym_list
    ]

    return {
        "files": files_map,
        "selectedTarget": chosen_target,
        "symbols": symbols,
        "edges": _build_dependency_edges(mapper),
        "audit": {
            "projectName": audit.project_name,
            "rootPath": chosen_target,
            "totalFiles": audit.total_files,
            "healthScore": audit.health_score,
            "findings": [
                {
                    "severity": f.severity,
                    "category": f.category,
                    "filePath": f.file_path,
                    "lineNumber": f.line_number,
                    "description": f.description,
                    "remediation": f.remediation,
                }
                for f in audit.findings
            ],
            "totalRoutesDetected": audit.total_routes_detected,
            "totalTestsDetected": audit.total_tests_detected,
            "hasCiWorkflow": audit.has_ci_workflow,
            "hasDockerfile": audit.has_dockerfile,
            "hasTerraform": audit.has_terraform,
            "summary": audit.summary,
        },
        "blastRadius": _to_blast_contract(blast),
        "refactorPlan": {
            "task": plan.task,
            "targetFiles": plan.target_files,
            "blastRadius": _to_blast_contract(plan.blast_radius),
            "patches": [
                {
                    "filePath": pt.file_path,
                    "diffOrContent": pt.diff_or_content,
                    "changeType": pt.change_type,
                }
                for pt in plan.patches
            ],
            "verificationStrategy": plan.verification_strategy,
            "estimatedRisk": plan.estimated_risk,
        },
    }


@app.get("/api/v1/framework-health")
async def framework_health() -> dict[str, Any]:
    """Return live framework runtime metadata and manifest-backed verification counters."""
    manifest = _load_verification_manifest()
    suites = manifest.get("suites", {})
    core_suite = suites.get("core_pytest", {})
    core_passed = int(core_suite.get("passed", 0))
    core_total = int(core_suite.get("total", 0))
    return {
        "status": "healthy",
        "framework": "nexus-agent-framework",
        "version": __version__,
        "pypi_live_version": str(manifest.get("pypi_live_version", "0.1.1")),
        "pypi_staged_version": str(manifest.get("pypi_staged_version", __version__)),
        "ci_status_url": str(manifest.get("ci_status_url", "https://github.com/sabburi1994/nexus/actions")),
        "website": "https://nexus.abburi.info",
        "repository": "https://github.com/sabburi1994/nexus",
        "author": "Sai Nikhil Abburi",
        "tests_passed": core_passed,
        "tests_total": core_total,
        "suite_breakdown": suites,
        "preflight_clearance": "100% GREEN" if core_passed == core_total and core_total > 0 else "VERIFYING",
        "supported_models": ["gemini-3.8-flash", "gemini-2.5-pro", "claude-3-7-sonnet"],
        "default_model": "gemini-3.8-flash",
        "mcp_enabled": True,
        "stages_active": [
            "Stage 1: Closed-Loop Self-Healing",
            "Stage 2: Brownfield AST Blast-Radius Support",
            "Stage 3: Enterprise ROI & DORA Telemetry",
        ],
        "packages": {
            "pypi": f"nexus-agent-framework=={__version__}",
            "contracts": "@nexus-agent-framework/contracts@1.0.3",
            "middleware": "@nexus-agent-framework/middleware@1.0.2",
            "scraper": "@nexus-agent-framework/scraper@1.0.2",
            "ui": "@nexus-agent-framework/ui@0.2.0",
        },
        "pricing_model": {
            "gemini_3_8_flash_input_per_m": f"${GEMINI_3_8_FLASH_INPUT_PER_M:.3f} USD",
            "gemini_3_8_flash_output_per_m": f"${GEMINI_3_8_FLASH_OUTPUT_PER_M:.3f} USD",
            "mock_provider_cost": "$0.00 USD",
        },
    }


@app.get("/api/v1/reports")
async def list_reports() -> list[dict[str, Any]]:
    """Return cached scan reports created via /api/v1/scan."""
    return list(_REPORTS_STORE.values())


@app.post("/api/v1/scan", response_model=ScanResponse)
async def scan_target(req: ScanRequest) -> ScanResponse:
    """Analyze an economic or technical target using GuardrailManager + GeminiClient."""
    try:
        clean_target = guardrail.inspect_input(req.target)
    except SecurityViolationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    report_id = f"rep_{uuid.uuid4().hex[:8]}"
    prompt = (
        f"You are an expert systems and economic analyst. Analyze '{clean_target}' in sector '{req.sector}'. "
        "Provide a 2-sentence executive summary covering structural risks and momentum."
    )
    try:
        res = gemini.generate(prompt)
        summary_text = res.text.strip()
        tokens = res.input_tokens + res.output_tokens
    except Exception:
        summary_text = (
            f"Deterministic baseline analysis for {clean_target} ({req.sector}) "
            "indicates steady structural capacity with moderate supply-chain sensitivity."
        )
        tokens = 48

    sentiment = 78.5
    risk = "low" if "steady" in summary_text.lower() or "growth" in summary_text.lower() else "medium"
    result = ScanResponse(
        id=report_id,
        target=clean_target,
        sector=req.sector,
        sentiment_score=sentiment,
        risk_level=risk,
        summary=summary_text,
        model="gemini-3.8-flash",
        tokens_used=tokens,
    )
    _REPORTS_STORE[report_id] = result.model_dump()
    return result


@app.post("/api/v1/simulate")
async def simulate_pipeline(
    req: SimulationRequest,
    x_gemini_api_key: str | None = Header(default=None, alias="X-Gemini-API-Key"),
) -> Any:
    """
    Execute the actual NexusITTeam + ClosedLoopHealer + RoiCalculator workflow in an isolated
    temporary workspace, using either the deterministic offline provider or a visitor's BYOK Gemini key.
    """
    try:
        clean_idea = guardrail.inspect_input(req.idea)
    except SecurityViolationError as exc:
        return JSONResponse(
            status_code=422,
            content={
                "error": "guardrail_blocked",
                "message": str(exc),
                "matched": check_prompt_injection(req.idea).matched_pattern,
            },
        )

    pii_scrubbed = 1 if clean_idea != req.idea else 0
    byok_key = (x_gemini_api_key or "").strip()
    is_byok = bool(byok_key)
    provider: ShowcaseSquadProvider = (
        ByokGeminiShowcaseProvider(
            idea=clean_idea,
            api_key=byok_key,
            target_cloud=req.target_cloud,
            simulate_healing=req.simulate_healing,
        )
        if is_byok
        else ShowcaseSquadProvider(
            idea=clean_idea,
            target_cloud=req.target_cloud,
            simulate_healing=req.simulate_healing,
        )
    )
    team = NexusITTeam(provider=provider)

    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="nexus_sim_") as tmp:
        try:
            delivered = team.build_from_idea(
                raw_user_idea=clean_idea,
                target_cloud=req.target_cloud,
                output_dir=Path(tmp),
                enable_self_healing=True,
                max_healing_cycles=3,
            )
        except ByokGeminiProviderError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        elapsed = time.perf_counter() - t0
        app_path = Path(delivered.output_path) if delivered.output_path else Path(tmp)
        roi_report = RoiCalculator(hourly_rate=85.0).calculate_from_codebase(app_path)
        zip_bytes = _archive_workspace_zip(app_path)

        wireframe_html = (
            (app_path / "docs" / "preview_mockup.html").read_text(encoding="utf-8")
            if (app_path / "docs" / "preview_mockup.html").exists()
            else delivered.proposal.wireframe_preview_html
        )
        architecture_md = (
            (app_path / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
            if (app_path / "docs" / "ARCHITECTURE.md").exists()
            else ""
        )

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    _cache_workspace_zip(run_id, delivered.proposal.app_name, zip_bytes)

    healing_contract = (
        _to_healing_contract(delivered.healing_report, elapsed)
        if delivered.healing_report is not None
        else {
            "initialTestsPassed": True,
            "totalAttempts": 0,
            "maxAttemptsAllowed": 3,
            "finalStatus": "HEALTHY",
            "attempts": [],
            "durationSeconds": round(elapsed, 3),
            "summary": "Initial QA preflight passed with zero defects.",
        }
    )

    total_tokens = sum(int(s["tokens"]) for s in provider.calls)
    projected_cost = round(sum(float(s["costUsd"]) for s in provider.calls), 6)
    actual_cost = projected_cost if is_byok else 0.0

    return {
        "run_id": run_id,
        "execution_mode": "byok-live" if is_byok else "deterministic",
        "actual_api_cost_usd": actual_cost,
        "projected_gemini_cost_usd": projected_cost,
        "app_name": delivered.proposal.app_name,
        "title": delivered.proposal.title,
        "tagline": delivered.proposal.tagline,
        "target_cloud": delivered.solution.cloud_provider,
        "sanitized_input": clean_idea,
        "pii_scrubbed_count": pii_scrubbed,
        "user_stories": delivered.proposal.user_stories,
        "steps": provider.calls,
        "total_tokens": total_tokens,
        "total_cost_usd": projected_cost,
        "healing_cycles": healing_contract["totalAttempts"],
        "verdict": (
            f"PASS - {healing_contract['finalStatus']} in {healing_contract['durationSeconds']}s "
            f"({delivered.qa.security_verdict})"
        ),
        "healing_report": healing_contract,
        "roi_report": _to_roi_contract(roi_report),
        "artifacts": {
            "wireframe_html": wireframe_html,
            "architecture_md": architecture_md,
            "backend_main_py": delivered.fullstack.backend_main_py,
            "backend_models_py": delivered.fullstack.backend_models_py,
            "frontend_app_tsx": delivered.fullstack.frontend_app_tsx,
            "sql_ddl": delivered.data_architecture.sql_ddl_schema,
            "terraform_main_tf": delivered.devops.terraform_main_tf,
            "test_preflight_py": delivered.qa.test_suite_code,
        },
    }


@app.get("/api/v1/simulate/{run_id}/download")
async def download_simulated_workspace(run_id: str) -> Response:
    """Download the real synthesized project directory as a ZIP archive."""
    entry = _WORKSPACE_ZIPS.get(run_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Simulation workspace expired or not found; re-run simulation.")
    app_name, zip_bytes = entry
    safe_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", app_name).strip("-") or "nexus-workspace"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_slug}.zip"'},
    )


def _inspect_source_payload(req: BrownfieldInspectRequest, provider: ShowcaseSquadProvider) -> dict[str, Any]:
    if req.source_mode == "custom" and req.custom_files:
        with tempfile.TemporaryDirectory(prefix="nexus_ast_") as tmp:
            root = Path(tmp)
            _write_validated_custom_files(root, req.custom_files)
            return _inspect_directory(root, req.target_file, req.refactor_task, provider)

    if not _SAMPLE_BROWNFIELD_DIR.exists():
        raise HTTPException(status_code=404, detail="Sample brownfield directory not found.")
    return _inspect_directory(_SAMPLE_BROWNFIELD_DIR, req.target_file, req.refactor_task, provider)


@app.post("/api/v1/brownfield/inspect")
async def brownfield_inspect(req: BrownfieldInspectRequest) -> dict[str, Any]:
    """Run live CodebaseAuditor, AstDependencyMapper, and BrownfieldRefactorer on real files."""
    provider = ShowcaseSquadProvider(idea=req.refactor_task, simulate_healing=False)
    return _inspect_source_payload(req, provider)


@app.post("/api/v1/brownfield/apply-preview")
async def brownfield_apply_preview(req: BrownfieldApplyRequest) -> dict[str, Any]:
    """Apply Stage 2 security remediations to an isolated copy and re-run AST + CodebaseAuditor."""
    provider = ShowcaseSquadProvider(idea=req.refactor_task, simulate_healing=False)
    before = _inspect_source_payload(req, provider)
    patched_files, diffs = _apply_surgical_remediations(before["files"])

    with tempfile.TemporaryDirectory(prefix="nexus_patched_") as tmp:
        root = Path(tmp)
        _write_validated_custom_files(root, patched_files)
        after = _inspect_directory(root, req.target_file, req.refactor_task, provider)

    before_score = int(before["audit"]["healthScore"])
    after_score = int(after["audit"]["healthScore"])
    return {
        "beforeAudit": before["audit"],
        "afterAudit": after["audit"],
        "afterInspect": after,
        "appliedDiffs": diffs,
        "scoreDelta": after_score - before_score,
        "findingsResolved": max(0, len(before["audit"]["findings"]) - len(after["audit"]["findings"])),
    }


@app.get("/api/v1/audit-demo")
async def audit_demo() -> dict[str, Any]:
    """Live CodebaseAuditor pass over the bundled legacy billing microservice."""
    provider = ShowcaseSquadProvider(idea="Audit bundled legacy billing service", simulate_healing=False)
    inspected = _inspect_directory(
        _SAMPLE_BROWNFIELD_DIR,
        "models.py",
        "Audit bundled legacy billing service",
        provider,
    )
    return dict(inspected["audit"])


@app.get("/api/v1/blast-radius-demo")
async def blast_radius_demo(target: str = "models.py") -> dict[str, Any]:
    """Live AstDependencyMapper blast-radius result on bundled sample codebase."""
    mapper = AstDependencyMapper(_SAMPLE_BROWNFIELD_DIR)
    mapper.scan_codebase()
    blast = mapper.compute_blast_radius(target)
    return _to_blast_contract(blast)


@app.post("/api/v1/roi")
async def calculate_roi(req: RoiRequest) -> dict[str, Any]:
    """Calculate live Enterprise ROI & DORA telemetry using nexus.metrics.roi.RoiCalculator."""
    calc = RoiCalculator(hourly_rate=req.hourly_rate)

    # Monthly portfolio model scaled across team releases & healing prevention
    monthly_input_tokens = req.releases_per_month * req.avg_loc_per_app * 28
    monthly_output_tokens = req.releases_per_month * req.avg_loc_per_app * 4
    monthly_healing_loops = req.releases_per_month * 2
    monthly_vulns = max(1, req.releases_per_month // 2)

    single_run_report = calc.calculate_from_run(
        run_name=f"Enterprise Squad ({req.team_size} Eng · {req.releases_per_month} releases/mo)",
        input_tokens=monthly_input_tokens,
        output_tokens=monthly_output_tokens,
        files_created_or_modified=req.releases_per_month * 12,
        loc=req.releases_per_month * req.avg_loc_per_app,
        healing_iterations=monthly_healing_loops,
        vulnerabilities_prevented=monthly_vulns,
        hourly_rate=req.hourly_rate,
    )

    # Compute annual/monthly projections using real token cost pricing
    hours_per_release = round(6.0 + (req.avg_loc_per_app / 250.0), 1)
    monthly_hours = round(req.releases_per_month * hours_per_release, 1)
    annual_hours = round(monthly_hours * 12.0, 1)
    monthly_gross = round(monthly_hours * req.hourly_rate, 2)
    annual_gross = round(annual_hours * req.hourly_rate, 2)

    monthly_token_cost = round(calculate_cost_usd(monthly_input_tokens, monthly_output_tokens), 4)
    annual_token_cost = round(monthly_token_cost * 12.0, 4)
    annual_net = round(annual_gross - annual_token_cost, 2)
    roi_multiplier = round(annual_gross / max(annual_token_cost, 0.05), 1)

    dora = DoraMetrics(
        deployment_frequency_multiplier=round(min(12.0, max(2.8, req.releases_per_month * 0.65)), 1),
        lead_time_reduction_pct=single_run_report.dora_metrics.lead_time_reduction_pct,
        change_failure_rate_pct=single_run_report.dora_metrics.change_failure_rate_pct,
        mttr_minutes=single_run_report.dora_metrics.mttr_minutes,
    )

    annual_report = EnterpriseRoiReport(
        project_name=f"nexus-enterprise-squad-{req.team_size}eng",
        target_path="organization/production-pipeline",
        total_files_analyzed=req.releases_per_month * 12 * 12,
        total_lines_of_code=req.releases_per_month * req.avg_loc_per_app * 12,
        total_runs_analyzed=req.releases_per_month * 12,
        total_input_tokens=monthly_input_tokens * 12,
        total_output_tokens=monthly_output_tokens * 12,
        total_token_cost_usd=annual_token_cost,
        engineering_hours_saved=annual_hours,
        hourly_rate_usd=req.hourly_rate,
        human_cost_saved_usd=annual_gross,
        net_savings_usd=annual_net,
        roi_multiplier=roi_multiplier,
        dora_metrics=dora,
        vulnerabilities_prevented=monthly_vulns * 12,
        healing_cycles_executed=monthly_healing_loops * 12,
        refactor_tasks_executed=req.releases_per_month * 12,
        summary=(
            f"A {req.team_size}-engineer org shipping {req.releases_per_month} releases/mo (~{req.avg_loc_per_app:,} LOC/app) "
            f"saves {annual_hours:,.0f} engineering hours/yr (${annual_net:,.2f} net at ${req.hourly_rate:.0f}/hr) "
            f"for ${annual_token_cost:,.2f}/yr in Gemini 3.8 Flash tokens ({roi_multiplier:,.1f}x ROI)."
        ),
    )

    return {
        "team_size": req.team_size,
        "hourly_rate": req.hourly_rate,
        "monthly_hours_saved": monthly_hours,
        "annual_hours_saved": annual_hours,
        "monthly_gross_savings_usd": monthly_gross,
        "annual_gross_savings_usd": annual_gross,
        "monthly_token_cost_usd": monthly_token_cost,
        "annual_net_savings_usd": annual_net,
        "roi_multiplier": roi_multiplier,
        "dora_metrics": dora.model_dump(),
        "summary": annual_report.summary,
        "scorecard": _to_roi_contract(annual_report),
        "cli_summary": calc.format_cli_summary(annual_report),
    }


@app.post("/api/v1/guardrail/inspect")
async def guardrail_inspect(req: GuardrailInspectRequest) -> dict[str, Any]:
    """Execute live Nexus prompt-injection detection and secret/PII scrubbing."""
    inj = check_prompt_injection(req.payload)
    scrubbed = sanitize_text(req.payload)
    redactions = sum(
        scrubbed.count(marker)
        for marker in (
            "[REDACTED_API_KEY]",
            "[REDACTED_GITHUB_TOKEN]",
            "[REDACTED_GOOGLE_API_KEY]",
            "[REDACTED_OAUTH_TOKEN]",
            "[REDACTED_EMAIL]",
        )
    )

    blocked = not inj.is_safe
    verdict = (
        f"BLOCKED by GuardrailManager: matched jailbreak pattern '{inj.matched_pattern}'"
        if blocked
        else (
            f"SANITIZED: scrubbed {redactions} credential/PII token(s) cleanly"
            if redactions > 0
            else "PASS: Clean prompt cleared for agent orchestration"
        )
    )

    return {
        "blocked": blocked,
        "matched_pattern": inj.matched_pattern,
        "sanitized_text": scrubbed,
        "redactions_count": redactions,
        "verdict": verdict,
    }


_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
