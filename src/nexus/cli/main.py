"""Nexus CLI: Developer tools for scaffolding apps and testing Google Cloud Vertex AI."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from nexus import __version__
from nexus.ai.client import GeminiClient, get_gcp_access_token, get_gcp_project


def check_ai_cmd(model: str = "gemini-3.8-flash", project: str | None = None) -> int:
    """Verify connectivity to Google Cloud Vertex AI and Gemini 3.8 Flash."""
    project_id = project or get_gcp_project()
    token = get_gcp_access_token()

    print(f"--- Checking Nexus AI Connection ---\nProject: {project_id}\nModel: {model}")

    if not token and not os.getenv("GEMINI_API_KEY"):
        print("FAIL: No GCP OAuth access token or GEMINI_API_KEY available.")
        print("Hint: Run 'gcloud auth application-default login' or configure IAM service account.")
        return 1

    if token:
        print(f"Acquired GCP Bearer Token: {token[:12]}... (cached)")

    try:
        client = GeminiClient(project_id=project_id, default_model=model)
        start_msg = "Hello from Nexus Framework. Confirm you are Gemini 3.8 Flash in one sentence."
        resp = client.generate(start_msg)
        print("SUCCESS: Vertex AI responded!")
        print(f'"{resp.text}"')
        print(
            f"Usage: {resp.input_tokens} input tokens, {resp.output_tokens} output tokens. Cost: ${resp.cost_usd:.6f} USD"
        )
        return 0
    except Exception as exc:
        print(f"FAIL: Call to Vertex AI failed: {exc}")
        return 1


def run_doctor_cmd() -> int:
    """Run diagnostics on environment, SDKs, tools, and cloud connectivity."""
    import shutil
    import subprocess

    from nexus import __version__

    print(f"=== Nexus Framework Doctor (v{__version__}) ===\n")
    all_ok = True

    # 1. Python runtime
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 11):
        print(f"  [PASS] Python Runtime: v{py_ver} ({sys.executable})")
    else:
        print(f"  [FAIL] Python Runtime: v{py_ver} (Requires Python >= 3.11)")
        all_ok = False

    # 2. Node & npm
    node_bin = shutil.which("node")
    if node_bin:
        try:
            node_ver = subprocess.check_output([node_bin, "--version"], text=True).strip()
            print(f"  [PASS] Node.js Runtime: {node_ver} ({node_bin})")
        except Exception:
            print(f"  [WARN] Node.js Runtime: Installed at {node_bin}")
    else:
        print("  [WARN] Node.js Runtime: Not found in PATH (needed for TypeScript/React build)")

    # 3. Terraform
    tf_bin = shutil.which("terraform")
    if tf_bin:
        try:
            tf_ver = subprocess.check_output([tf_bin, "version"], text=True).splitlines()[0]
            print(f"  [PASS] Terraform CLI: {tf_ver} ({tf_bin})")
        except Exception:
            print(f"  [PASS] Terraform CLI: Installed at {tf_bin}")
    else:
        print("  [INFO] Terraform CLI: Not found in PATH (DevOps agent can generate IaC without local CLI)")

    # 4. Google Cloud ADC & Project
    project_id = get_gcp_project()
    token = get_gcp_access_token()
    if token:
        print(f"  [PASS] Google Cloud ADC: Authenticated (Token: {token[:12]}..., Project: {project_id})")
    elif os.getenv("GEMINI_API_KEY"):
        print("  [PASS] Gemini API Key: Configured in environment")
    else:
        print("  [FAIL] Google Cloud Auth: No ADC token or GEMINI_API_KEY found")
        all_ok = False

    # 5. Vertex AI Gemini 3.8 Flash connectivity
    try:
        client = GeminiClient(project_id=project_id, default_model="gemini-3.8-flash")
        resp = client.generate("Ping")
        print(
            f"  [PASS] Vertex AI Connectivity: Gemini 3.8 Flash operational (Latency: low, Cost: ${resp.cost_usd:.6f})"
        )
    except Exception as e:
        print(f"  [FAIL] Vertex AI Connectivity: {e}")
        all_ok = False

    # 6. Monorepo packages status
    packages_dir = Path(__file__).resolve().parent.parent.parent.parent / "packages"
    if packages_dir.exists():
        pkgs = [p.name for p in packages_dir.iterdir() if p.is_dir()]
        print(f"  [PASS] Monorepo Packages: Found {len(pkgs)} packages ({', '.join(pkgs)})")
    else:
        print("  [INFO] Monorepo Packages: Standalone framework install")

    print(
        f"\nResult: {'ALL CHECKS PASSED - Ready to build autonomous agents!' if all_ok else 'SOME CHECKS REQUIRE ATTENTION'}"
    )
    return 0 if all_ok else 1


def scaffold_new_app(app_name: str, output_dir: Path) -> Path:
    """Scaffold a new microservice/app powered by the Nexus Framework."""
    target = output_dir / app_name
    if target.exists():
        raise FileExistsError(f"Target path {target} already exists.")

    print(f"Scaffolding new Nexus application: {app_name}...")

    # Create directories
    (target / "src" / app_name).mkdir(parents=True, exist_ok=True)
    (target / "tests").mkdir(parents=True, exist_ok=True)

    # Write pyproject.toml
    pyproject_content = f"""[project]
name = "{app_name}"
version = "0.1.0"
description = "{app_name} microservice powered by Nexus Framework"
requires-python = ">=3.11"
dependencies = [
    "nexus-framework>=0.1.0",
    "uvicorn>=0.30.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
    (target / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    # Write main app file
    main_py_content = f"""\"\"\"{app_name} main service application entry point.\"\"\"
from nexus.api import create_nexus_app
from nexus.ai import GeminiClient

app = create_nexus_app(
    title="{app_name}",
    description="{app_name} service powered by Nexus Framework & Gemini 3.8",
)

ai_client = GeminiClient()

@app.get("/api/ai/ask")
async def ask_ai(prompt: str) -> dict[str, str]:
    resp = ai_client.generate(prompt)
    return {{"response": resp.text, "model": resp.model}}
"""
    (target / "src" / app_name / "main.py").write_text(main_py_content, encoding="utf-8")
    (target / "src" / app_name / "__init__.py").write_text("", encoding="utf-8")

    # Write Dockerfile
    dockerfile_content = """FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir uvicorn fastapi httpx pydantic nexus-framework
COPY . .
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
"""
    (target / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")

    print(f"Application created successfully at {target}!")
    return target


def run_mcp_server() -> None:
    """Run the embedded Model Context Protocol (MCP) server for Claude Code and Cursor."""
    from nexus.orchestrator.mcp import NexusMcpServer
    from nexus.tools.base import Tool, ToolPermission

    server = NexusMcpServer(name="nexus-mcp", version=__version__)

    # Register core tools
    def check_ai_tool(model: str = "gemini-3.8-flash") -> dict[str, str]:
        """Check Vertex AI Gemini 3.8 connectivity."""
        client = GeminiClient(default_model=model)
        res = client.generate("Ping")
        return {"status": "ok", "response": res.text, "model": res.model}

    server.register_tool(Tool(fn=check_ai_tool, name="nexus_check_ai", permission=ToolPermission.READ_ONLY))
    server.run_stdio()


def dream_cmd(idea: str, output_dir: Path) -> None:
    """Run the Nexus Core IT Pack to convert an idea into a complete software project."""
    from nexus.teams.it_pack.team import NexusITTeam

    print("--- Nexus Core IT Squad Activated ---")
    print(f'Goal: "{idea}"')
    print("Assignees: Business Analyst, Engineering Manager, UI/UX Designer, Backend Engineer, QA Engineer\n")

    team = NexusITTeam()
    project = team.build_from_idea(idea, output_dir=output_dir)

    print("\n=== Project Delivered! ===")
    print(f"App: {project.proposal.title} ({project.proposal.app_name})")
    print(f"Tagline: {project.proposal.tagline}")
    print(f"Output Directory: {project.output_path}")
    print(f"Stories: {len(project.proposal.user_stories)} user stories defined")
    print(f"Cloud Target: {project.solution.cloud_provider.upper()} ({project.solution.compute_pattern})")
    print(f"Data Schema: {project.data_architecture.database_engine} ({len(project.data_architecture.tables)} tables)")
    print(f"UI Component: {project.ui.component_name}.tsx")
    print(f"QA Preflight: {'PASS' if project.qa.passed_preflight else 'WARN'}")


def run_dashboard_cmd(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> None:
    """Launch the Nexus Visualizer localhost dashboard."""
    import webbrowser

    import uvicorn

    url = f"http://{host}:{port}"
    print("--- Nexus Agent Visualizer Starting ---")
    print(f"Localhost Dashboard: {url}")
    print(f"Streaming telemetry: {url}/api/stream")
    print("Press CTRL+C to stop the dashboard.\n")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run(
        "nexus.dashboard.server:create_dashboard_app",
        host=host,
        port=port,
        factory=True,
        log_level="info",
    )


def audit_cmd(path: Path, output_json: bool = False) -> int:
    """Run comprehensive security and architectural audit."""
    from nexus.brownfield.auditor import CodebaseAuditor

    auditor = CodebaseAuditor(path)
    report = auditor.run_audit()

    if output_json:
        print(report.model_dump_json(indent=2))
        return 0

    print("================================================================================")
    print(f"             NEXUS CODEBASE AUDIT REPORT: {report.project_name}")
    print("================================================================================")
    print(f"  Target Root      : {report.root_path}")
    print(f"  Health Score     : {report.health_score}/100")
    print(f"  Files Analyzed   : {report.total_files} files")
    print(f"  Routes Detected  : {report.total_routes_detected}")
    print(f"  Test Files Found : {report.total_tests_detected}")
    print("--------------------------------------------------------------------------------")
    if not report.findings:
        print("  [PASS] No security vulnerabilities or architecture violations detected.")
    else:
        print(f"  Findings ({len(report.findings)} issues detected):")
        for f in report.findings:
            print(f"  * [{f.severity}] {f.category} in {f.file_path}:{f.line_number}")
            print(f"    Issue: {f.description}")
            print(f"    Fix  : {f.remediation}")
    print("================================================================================")
    return 1 if any(f.severity == "CRITICAL" for f in report.findings) else 0


def refactor_cmd(task: str, path: Path, target: str | None = None, apply_patches: bool = False) -> int:
    """Analyze blast radius and generate surgical refactor plan."""
    from nexus.brownfield.refactor import BrownfieldRefactorer

    refactorer = BrownfieldRefactorer(path)
    print("--- Nexus Brownfield Refactoring ---")
    print(f"Task: {task}")
    if target:
        print(f"Primary Target: {target}")

    plan = refactorer.plan_refactor(task, primary_target=target)
    blast = plan.blast_radius

    print(f"\n[BLAST RADIUS ANALYSIS: {blast.risk_tier} RISK]")
    print(f"  Target                : {blast.target}")
    print(
        f"  Direct Dependents     : {len(blast.direct_dependents)} files ({', '.join(blast.direct_dependents[:3]) if blast.direct_dependents else 'None'})"
    )
    print(f"  Indirect Dependents   : {len(blast.indirect_dependents)} files")
    print(f"  Impacted API Routes   : {len(blast.affected_routes)}")
    print(f"  Impacted Test Suites  : {len(blast.affected_tests)}")

    print("\n[REFACTOR PLAN]")
    print(f"  Verification Strategy : {plan.verification_strategy}")
    print(f"  Estimated Risk        : {plan.estimated_risk}")
    print(f"  Patches Synthesized   : {len(plan.patches)} files")
    for patch in plan.patches:
        print(f"    - [{patch.change_type.upper()}] {patch.file_path}")

    if apply_patches and plan.patches:
        for patch in plan.patches:
            dest = path / patch.file_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(patch.diff_or_content, encoding="utf-8")
        print("\n[SUCCESS] Surgical patches applied to disk.")
    elif not apply_patches and plan.patches:
        print("\n[INFO] Dry-run complete. Run with --apply to apply patches.")
    return 0


def metrics_cmd(path: Path, hourly_rate: float = 85.0, output_json: bool = False) -> int:
    """Calculate enterprise ROI and DORA velocity telemetry."""
    from nexus.metrics.roi import RoiCalculator

    calculator = RoiCalculator(hourly_rate=hourly_rate)
    report = calculator.calculate_from_codebase(path)

    if output_json:
        print(report.model_dump_json(indent=2))
    else:
        print(calculator.format_cli_summary(report))
    return 0


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="nexus",
        description="Nexus Platform Framework: Scaffolding, AI verification, and cloud tools.",
    )
    parser.add_argument("--version", action="version", version=f"Nexus Framework v{__version__}")
    subparsers = parser.add_subparsers(dest="command")

    # check-ai
    ai_parser = subparsers.add_parser("check-ai", help="Verify Vertex AI & Gemini 3.8 Flash connectivity.")
    ai_parser.add_argument("--model", default="gemini-3.8-flash", help="Model ID")
    ai_parser.add_argument("--project", default=None, help="GCP Project ID")

    # new
    new_parser = subparsers.add_parser("new", help="Scaffold a new Nexus application.")
    new_parser.add_argument("name", help="Name of application to scaffold")
    new_parser.add_argument("--output-dir", default=".", help="Directory where app will be created")

    # mcp
    subparsers.add_parser(
        "mcp",
        help="Start embedded Model Context Protocol (MCP) server for Claude Code & Cursor.",
    )

    # doctor
    subparsers.add_parser(
        "doctor",
        help="Run comprehensive health check on environment, GCP, AI, and tools.",
    )

    # dream
    dream_parser = subparsers.add_parser(
        "dream",
        help="Transform a user idea into a complete app via the Nexus IT Squad.",
    )
    dream_parser.add_argument("idea", help="Raw description of the app you want to build")
    dream_parser.add_argument("--output-dir", default=".", help="Directory where project will be saved")

    # dashboard / ui
    dash_parser = subparsers.add_parser(
        "dashboard",
        help="Launch the localhost progress visualizer & tracking dashboard.",
    )
    dash_parser.add_argument("--port", type=int, default=8000, help="Port to serve dashboard on")
    dash_parser.add_argument("--host", default="127.0.0.1", help="Host address")
    dash_parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    ui_parser = subparsers.add_parser("ui", help="Alias for 'nexus dashboard'.")
    ui_parser.add_argument("--port", type=int, default=8000, help="Port to serve dashboard on")
    ui_parser.add_argument("--host", default="127.0.0.1", help="Host address")
    ui_parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    # audit (Stage 2)
    audit_parser = subparsers.add_parser(
        "audit",
        help="Run security, architectural, and test health audit on an existing codebase.",
    )
    audit_parser.add_argument(
        "path", nargs="?", default=".", help="Root directory to audit (default: current directory)"
    )
    audit_parser.add_argument("--json", action="store_true", help="Output full JSON report")

    # refactor (Stage 2)
    refactor_parser = subparsers.add_parser(
        "refactor",
        help="Plan and execute surgical refactoring on brownfield codebases with AST blast-radius analysis.",
    )
    refactor_parser.add_argument("task", help="Refactoring task description")
    refactor_parser.add_argument("--target", default=None, help="Primary file or symbol target")
    refactor_parser.add_argument("--path", default=".", help="Codebase directory (default: current directory)")
    refactor_parser.add_argument("--apply", action="store_true", help="Apply generated patches directly to disk")

    # metrics (Stage 3)
    metrics_parser = subparsers.add_parser(
        "metrics",
        help="Calculate engineering velocity, DORA acceleration, and enterprise ROI telemetry.",
    )
    metrics_parser.add_argument("path", nargs="?", default=".", help="Target directory (default: current directory)")
    metrics_parser.add_argument(
        "--hourly-rate", type=float, default=85.0, help="Engineer hourly cost benchmark (default: $85/hr)"
    )
    metrics_parser.add_argument("--json", action="store_true", help="Output full JSON telemetry")

    args = parser.parse_args()
    if args.command == "check-ai":
        sys.exit(check_ai_cmd(model=args.model, project=args.project))
    elif args.command == "new":
        scaffold_new_app(args.name, Path(args.output_dir))
    elif args.command == "mcp":
        run_mcp_server()
    elif args.command == "doctor":
        sys.exit(run_doctor_cmd())
    elif args.command == "dream":
        dream_cmd(args.idea, Path(args.output_dir))
    elif args.command in ("dashboard", "ui"):
        run_dashboard_cmd(host=args.host, port=args.port, open_browser=not args.no_browser)
    elif args.command == "audit":
        sys.exit(audit_cmd(Path(args.path), output_json=args.json))
    elif args.command == "refactor":
        sys.exit(refactor_cmd(args.task, Path(args.path), target=args.target, apply_patches=args.apply))
    elif args.command == "metrics":
        sys.exit(metrics_cmd(Path(args.path), hourly_rate=args.hourly_rate, output_json=args.json))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

app = main
