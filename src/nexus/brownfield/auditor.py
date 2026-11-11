"""Nexus Brownfield: Comprehensive codebase health, security, and architecture auditor."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import BaseModel, Field

from nexus.brownfield.analyzer import AstDependencyMapper
from nexus.security.guardrail import GuardrailManager
from nexus.security.sanitizer import sanitize_text

logger = logging.getLogger("nexus.brownfield.auditor")


class SecurityFinding(BaseModel):
    """Identified vulnerability or secret exposure."""

    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    category: str  # "SECRET_LEAK", "PROMPT_INJECTION", "MISSING_GUARDRAIL"
    file_path: str
    line_number: int
    description: str
    remediation: str


class CodebaseAuditReport(BaseModel):
    """Complete health, security, and dependency audit for a brownfield codebase."""

    project_name: str
    root_path: str
    total_files: int
    health_score: int = Field(ge=0, le=100)
    findings: list[SecurityFinding] = Field(default_factory=list)
    total_routes_detected: int = 0
    total_tests_detected: int = 0
    has_ci_workflow: bool = False
    has_dockerfile: bool = False
    has_terraform: bool = False
    summary: str = ""


class CodebaseAuditor:
    """
    Audits existing repositories for:
    - Secret leaks and hardcoded keys.
    - AI injection vulnerabilities and missing guardrails.
    - Test coverage ratio and architecture drift.
    """

    def __init__(self, root_dir: Path | str) -> None:
        self.root_dir = Path(root_dir).resolve()
        self.guardrail = GuardrailManager()
        self.mapper = AstDependencyMapper(self.root_dir)

    def run_audit(self) -> CodebaseAuditReport:
        """Execute full static and architectural audit."""
        self.mapper.scan_codebase()

        findings: list[SecurityFinding] = []
        total_files = 0
        total_routes = 0
        total_tests = 0

        # Check CI / Docker / Terraform presence
        has_ci = (self.root_dir / ".github" / "workflows").exists()
        has_docker = (self.root_dir / "Dockerfile").exists() or (self.root_dir / "docker-compose.yml").exists()
        has_tf = any(self.root_dir.glob("*.tf")) or (self.root_dir / "infra").exists()

        for path in self.root_dir.rglob("*"):
            if path.is_dir():
                continue
            if any(
                p.startswith(".") or p in ("__pycache__", "node_modules", "venv", ".venv", "dist") for p in path.parts
            ):
                continue

            total_files += 1
            rel_path = str(path.relative_to(self.root_dir)).replace("\\", "/")

            if "test" in path.name.lower():
                total_tests += 1

            # Only scan text files for secrets
            if path.suffix in (".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".env", ".toml"):
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                # 1. Secret scanning
                for line_no, line in enumerate(content.splitlines(), start=1):
                    # Check for hardcoded API keys
                    if any(prefix in line for prefix in ("sk-", "ghp_", "AKIA", "AIzaSy")):
                        # Check if line contains literal secret
                        sanitized = sanitize_text(line)
                        if "[REDACTED" in sanitized:
                            findings.append(
                                SecurityFinding(
                                    severity="CRITICAL",
                                    category="SECRET_LEAK",
                                    file_path=rel_path,
                                    line_number=line_no,
                                    description="Exposed credential or private API token detected.",
                                    remediation="Move secret to environment variable or Secret Manager.",
                                )
                            )

                    # 2. Check unvalidated direct AI client calls
                    if (
                        ("GeminiClient" in line or "OpenAI" in line)
                        and "sanitize" not in content
                        and "guardrail" not in content
                    ):
                        findings.append(
                            SecurityFinding(
                                severity="HIGH",
                                category="MISSING_GUARDRAIL",
                                file_path=rel_path,
                                line_number=line_no,
                                description="AI model invoked without deterministic GuardrailManager sanitization.",
                                remediation="Wrap prompt inputs with GuardrailManager.sanitize_text().",
                            )
                        )
                        break

        # Count routes from mapper
        for syms in self.mapper.symbols_map.values():
            for s in syms:
                if s.kind == "route":
                    total_routes += 1

        # Calculate score (100 base, subtract for issues)
        score = 100
        for f in findings:
            if f.severity == "CRITICAL":
                score -= 25
            elif f.severity == "HIGH":
                score -= 10
            elif f.severity == "MEDIUM":
                score -= 5

        if total_routes > 0 and total_tests == 0:
            score -= 15
            findings.append(
                SecurityFinding(
                    severity="HIGH",
                    category="MISSING_TESTS",
                    file_path="tests/",
                    line_number=0,
                    description=f"{total_routes} API routes detected with 0 automated test suites.",
                    remediation="Generate test suite using 'nexus dream' QA specialist or pytest.",
                )
            )

        score = max(0, min(100, score))

        summary = (
            f"Audit finished: {total_files} files analyzed. "
            f"Health Score: {score}/100 with {len(findings)} findings. "
            f"Routes: {total_routes}, Tests: {total_tests}."
        )

        return CodebaseAuditReport(
            project_name=self.root_dir.name,
            root_path=str(self.root_dir),
            total_files=total_files,
            health_score=score,
            findings=findings,
            total_routes_detected=total_routes,
            total_tests_detected=total_tests,
            has_ci_workflow=has_ci,
            has_dockerfile=has_docker,
            has_terraform=has_tf,
            summary=summary,
        )
