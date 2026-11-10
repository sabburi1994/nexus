"""Tests for Nexus Stage 3: Enterprise ROI & DORA Telemetry."""

from __future__ import annotations

from pathlib import Path
import pytest

from nexus.metrics.roi import DoraMetrics, EnterpriseRoiReport, RoiCalculator


def test_roi_calculator_codebase(tmp_path: Path) -> None:
    # Create sample codebase structure
    src = tmp_path / "src"
    src.mkdir()
    app = src / "app.py"
    app.write_text("def run():\n    return 'ok'\n" * 20, encoding="utf-8")

    tests = tmp_path / "tests"
    tests.mkdir()
    test_file = tests / "test_app.py"
    test_file.write_text("def test_run():\n    assert True\n" * 10, encoding="utf-8")

    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM python:3.12-slim\nCMD ['python', 'src/app.py']\n", encoding="utf-8")

    calculator = RoiCalculator(hourly_rate=90.0)
    report = calculator.calculate_from_codebase(tmp_path)

    assert report.total_files_analyzed >= 3
    assert report.total_lines_of_code > 10
    assert report.engineering_hours_saved > 0
    assert report.hourly_rate_usd == 90.0
    assert report.human_cost_saved_usd > 0
    assert report.roi_multiplier > 1.0
    assert report.net_savings_usd > 0
    assert report.dora_metrics.deployment_frequency_multiplier >= 1.0
    assert report.dora_metrics.lead_time_reduction_pct > 50.0


def test_roi_calculator_run() -> None:
    calculator = RoiCalculator(hourly_rate=100.0)
    report = calculator.calculate_from_run(
        run_name="FullStack-Healing-Run",
        input_tokens=50_000,
        output_tokens=10_000,
        files_created_or_modified=5,
        loc=400,
        healing_iterations=2,
        vulnerabilities_prevented=2,
    )

    assert report.project_name == "FullStack-Healing-Run"
    assert report.engineering_hours_saved == 6.0 + 4.0 + 8.0  # 18.0 hours
    assert report.human_cost_saved_usd == 1800.00
    assert report.total_token_cost_usd > 0
    assert report.roi_multiplier > 50.0
    assert report.vulnerabilities_prevented == 2
    assert report.healing_cycles_executed == 2


def test_roi_format_cli_summary(tmp_path: Path) -> None:
    f = tmp_path / "main.py"
    f.write_text("print('hello')\n", encoding="utf-8")

    calculator = RoiCalculator()
    report = calculator.calculate_from_codebase(tmp_path)
    summary_text = calculator.format_cli_summary(report)

    assert "NEXUS ENTERPRISE TELEMETRY" in summary_text
    assert "NET ROI MULTIPLIER" in summary_text
    assert "DORA VELOCITY ACCELERATION" in summary_text
    assert "FINANCIAL ROI & EFFICIENCY" in summary_text
