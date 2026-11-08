"""Tests for the Nexus Core IT Pack."""
from __future__ import annotations

from pathlib import Path
from nexus.providers.mock import MockProvider
from nexus.teams.it_pack.ba import BusinessAnalystAgent, ProductProposal
from nexus.teams.it_pack.designer import UiDesignerAgent, UiSpecification
from nexus.teams.it_pack.engineer import BackendEngineerAgent, BackendSpecification
from nexus.teams.it_pack.manager import EngineeringManagerAgent, EngineeringTask, SprintPlan
from nexus.teams.it_pack.qa import QaEngineerAgent, QaSpecification
from nexus.teams.it_pack.team import NexusITTeam


def test_business_analyst_agent() -> None:
    """Verify BA generates structured ProductProposal."""
    mock_proposal = ProductProposal(
        app_name="watchhub",
        title="WatchHub",
        tagline="Luxury watch tracker across European marketplaces",
        target_audience="Watch collectors",
        user_stories=["As a buyer, I want price alerts"],
        core_features=["Real-time price index", "Fraud verification"],
        ui_concept="Dark mode dashboard with watch cards",
        wireframe_preview_html="<div>WatchHub Mockup</div>",
    )
    provider = MockProvider(structured_mock=mock_proposal)
    ba = BusinessAnalystAgent(provider)
    res = ba.analyze_requirements("I want an app that tracks luxury watches")
    assert res.app_name == "watchhub"
    assert len(res.user_stories) == 1


def test_it_team_build_from_idea(tmp_path: Path) -> None:
    """Verify NexusITTeam coordinates squad and writes project to disk."""
    mock_proposal = ProductProposal(
        app_name="watchhub",
        title="WatchHub",
        tagline="Luxury watch tracker",
        target_audience="Collectors",
        user_stories=["As a user, I want price alerts"],
        core_features=["Price alerts"],
        ui_concept="Dashboard",
        wireframe_preview_html="<div>Mockup</div>",
    )
    mock_plan = SprintPlan(
        architecture_overview="FastAPI + PostgreSQL + Gemini 3.8",
        database_entities=["Watch", "PriceAlert"],
        api_endpoints=["GET /api/watches - list watches"],
        tasks=[EngineeringTask(task_id="TASK-1", title="Setup DB", assignee="Backend Engineer", description="Create models")],
        estimated_tokens_needed=5000,
    )
    mock_ui = UiSpecification(
        component_name="WatchDashboard",
        color_palette="dark slate",
        react_code="export default function WatchDashboard() { return <div>Watches</div>; }",
    )
    mock_backend = BackendSpecification(
        entry_point_code="from fastapi import FastAPI\napp = FastAPI()",
        models_code="from pydantic import BaseModel\nclass Watch(BaseModel): name: str",
    )
    mock_qa = QaSpecification(
        test_suite_code="def test_health(): assert True",
        security_verdict="All guardrails pass",
        passed_preflight=True,
    )

    # Custom mock provider that cycles mocks
    class ITMockProvider(MockProvider):
        def structured(self, prompt: str, response_model: type, **kwargs):
            if response_model == ProductProposal:
                return mock_proposal
            if response_model == SprintPlan:
                return mock_plan
            if response_model == UiSpecification:
                return mock_ui
            if response_model == BackendSpecification:
                return mock_backend
            if response_model == QaSpecification:
                return mock_qa
            return super().structured(prompt, response_model, **kwargs)

    team = NexusITTeam(provider=ITMockProvider())
    out_dir = tmp_path / "delivered"
    out_dir.mkdir(parents=True, exist_ok=True)

    project = team.build_from_idea("I want a watch tracking app", output_dir=out_dir)

    assert project.proposal.app_name == "watchhub"
    assert project.output_path is not None
    app_path = Path(project.output_path)
    assert (app_path / "docs" / "PROPOSAL.md").exists()
    assert (app_path / "docs" / "SPRINT_PLAN.md").exists()
    assert (app_path / "frontend" / "src" / "WatchDashboard.tsx").exists()
    assert (app_path / "backend" / "src" / "main.py").exists()
    assert (app_path / "backend" / "tests" / "test_api.py").exists()
