"""Tests for Nexus Stage 2: Brownfield Legacy Codebase Support."""

from __future__ import annotations

from pathlib import Path

from nexus.brownfield.analyzer import AstDependencyMapper
from nexus.brownfield.auditor import CodebaseAuditor
from nexus.brownfield.refactor import BrownfieldRefactorer
from nexus.providers.mock import MockProvider


def test_ast_dependency_mapper(tmp_path: Path) -> None:
    # Create sample codebase with dependencies
    models_file = tmp_path / "models.py"
    models_file.write_text("class User:\n    pass\n", encoding="utf-8")

    api_file = tmp_path / "api.py"
    api_file.write_text("from models import User\n\ndef get_user():\n    return User()\n", encoding="utf-8")

    test_file = tmp_path / "test_api.py"
    test_file.write_text("import api\n\ndef test_get():\n    assert api.get_user()\n", encoding="utf-8")

    mapper = AstDependencyMapper(tmp_path)
    scan_info = mapper.scan_codebase()

    assert scan_info["total_files_analyzed"] >= 3

    # Check blast radius for models.py
    blast = mapper.compute_blast_radius("models.py")
    assert "api.py" in blast.direct_dependents or "api.py" in str(blast.direct_dependents)
    assert blast.risk_tier in ("LOW", "MEDIUM", "HIGH")


def test_codebase_auditor(tmp_path: Path) -> None:
    # Create clean repo
    src = tmp_path / "src"
    src.mkdir()
    main = src / "main.py"
    main.write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\ndef health(): return {}\n", encoding="utf-8"
    )

    auditor = CodebaseAuditor(tmp_path)
    report = auditor.run_audit()

    assert report.total_files >= 1
    assert report.health_score <= 100
    assert report.total_routes_detected >= 1


def test_codebase_auditor_detects_secret(tmp_path: Path) -> None:
    bad_file = tmp_path / "config.py"
    bad_file.write_text("OPENAI_KEY = 'sk-1234567890abcdef1234567890abcdef'\n", encoding="utf-8")

    auditor = CodebaseAuditor(tmp_path)
    report = auditor.run_audit()

    # Secret should be detected
    secret_findings = [f for f in report.findings if f.category == "SECRET_LEAK"]
    assert len(secret_findings) >= 1
    assert report.health_score < 100


def test_brownfield_refactorer(tmp_path: Path) -> None:
    f = tmp_path / "main.py"
    f.write_text("def hello(): return 'world'\n", encoding="utf-8")

    provider = MockProvider()
    refactorer = BrownfieldRefactorer(tmp_path, provider=provider)
    plan = refactorer.plan_refactor("Add caching to hello function", primary_target="main.py")

    assert plan.task == "Add caching to hello function"
    assert plan.blast_radius is not None
