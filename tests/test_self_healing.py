"""Tests for Nexus Stage 1: Closed-Loop Self-Healing."""

from __future__ import annotations

import pytest

from nexus.maintenance.healing_loop import ClosedLoopHealer, SelfHealingReport
from nexus.providers.mock import MockProvider
from nexus.teams.it_pack.ba import ProductProposal
from nexus.teams.it_pack.fullstack import FullStackEngineerAgent, FullStackSpecification
from nexus.teams.it_pack.qa import QaEngineerAgent, QaSpecification
from nexus.teams.it_pack.solution_architect import SolutionBlueprint
from nexus.teams.it_pack.team import NexusITTeam


def test_closed_loop_healer_when_already_passed() -> None:
    provider = MockProvider()
    healer = ClosedLoopHealer(provider=provider, max_healing_cycles=3)

    proposal = ProductProposal(
        title="Test App",
        app_name="testapp",
        tagline="Test Tagline",
        target_audience="Developers",
        problem_statement="Problem",
        core_features=["Auth", "API"],
        user_stories=["As a user..."],
        ui_concept="Clean dashboard",
        wireframe_preview_html="<div>Wireframe</div>",
    )
    solution = SolutionBlueprint(
        compute_pattern="Serverless",
        cloud_provider="gcp",
        system_topology="Cloud Run + Cloud SQL",
        non_functional_requirements=["High availability"],
        integration_services=["Cloud Logging"],
        latency_budget_ms=100,
    )
    fullstack = FullStackSpecification(
        backend_main_py="print('hello')",
        backend_models_py="class M: pass",
        frontend_app_tsx="export default function App() {}",
        frontend_api_client_ts="export async function fetchApi() {}",
    )
    qa = QaSpecification(
        test_suite_code="def test_ok(): assert True",
        security_verdict="All clear",
        passed_preflight=True,
    )

    fullstack_agent = FullStackEngineerAgent(provider)
    qa_agent = QaEngineerAgent(provider)

    fs_res, qa_res, report = healer.run_healing_loop(
        proposal=proposal,
        solution=solution,
        fullstack=fullstack,
        qa=qa,
        fullstack_agent=fullstack_agent,
        qa_agent=qa_agent,
    )

    assert report.was_healing_required is False
    assert report.resolved is True
    assert qa_res.passed_preflight is True


def test_closed_loop_healing_activates_on_failure() -> None:
    provider = MockProvider()
    healer = ClosedLoopHealer(provider=provider, max_healing_cycles=2)

    proposal = ProductProposal(
        title="Payment Service",
        app_name="payments",
        tagline="Pay seamlessly",
        target_audience="Merchants",
        problem_statement="Slow payments",
        core_features=["Stripe"],
        user_stories=["As a merchant..."],
        ui_concept="Payment form",
        wireframe_preview_html="<div>Payment Mockup</div>",
    )
    solution = SolutionBlueprint(
        compute_pattern="Serverless",
        cloud_provider="gcp",
        system_topology="Cloud Run",
        non_functional_requirements=["Scalable to 10k RPS"],
        integration_services=[],
        latency_budget_ms=150,
    )
    fullstack = FullStackSpecification(
        backend_main_py="buggy code",
        backend_models_py="",
        frontend_app_tsx="",
        frontend_api_client_ts="",
    )
    # QA initially failed
    qa_initial = QaSpecification(
        test_suite_code="def test_pay(): assert False",
        security_verdict="Syntax error detected in backend",
        passed_preflight=False,
    )

    fullstack_agent = FullStackEngineerAgent(provider)
    qa_agent = QaEngineerAgent(provider)

    fs_res, qa_res, report = healer.run_healing_loop(
        proposal=proposal,
        solution=solution,
        fullstack=fullstack,
        qa=qa_initial,
        fullstack_agent=fullstack_agent,
        qa_agent=qa_agent,
    )

    assert report.was_healing_required is True
    assert len(report.attempts) > 0
    assert report.total_cycles >= 1


def test_it_team_integration_with_self_healing() -> None:
    provider = MockProvider()
    team = NexusITTeam(provider=provider)

    delivered = team.build_from_idea(
        raw_user_idea="A real-time telemetry analytics platform",
        enable_self_healing=True,
    )

    assert delivered.proposal is not None
    assert delivered.fullstack is not None
    assert delivered.qa is not None
