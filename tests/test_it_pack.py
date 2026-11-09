"""Tests for the Nexus Core IT Pack."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nexus.providers.mock import MockProvider
from nexus.teams.it_pack.ba import BusinessAnalystAgent, ProductProposal
from nexus.teams.it_pack.data_architect import DataArchitecture
from nexus.teams.it_pack.designer import UiSpecification
from nexus.teams.it_pack.devops import DevopsSpecification
from nexus.teams.it_pack.fullstack import FullStackSpecification
from nexus.teams.it_pack.qa import QaSpecification
from nexus.teams.it_pack.solution_architect import SolutionBlueprint
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
    """Verify NexusITTeam coordinates 7 specialists and writes project with Terraform."""
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
    mock_solution = SolutionBlueprint(
        cloud_provider="gcp",
        compute_pattern="Cloud Run Serverless",
        system_topology="React -> Cloud Run FastAPI -> Cloud SQL",
        non_functional_requirements=["High availability"],
        integration_services=["Vertex AI", "Secret Manager"],
    )
    mock_data = DataArchitecture(
        database_engine="PostgreSQL 16",
        tables=["watches", "alerts"],
        relationships=["watches 1:N alerts"],
        indexes=["idx_watches_brand"],
        sql_ddl_schema="CREATE TABLE watches (id UUID PRIMARY KEY, name TEXT);",
    )
    mock_ui = UiSpecification(
        component_name="WatchDashboard",
        color_palette="dark slate",
        react_code="export default function WatchDashboard() { return <div>Watches</div>; }",
    )
    mock_fullstack = FullStackSpecification(
        backend_main_py="from fastapi import FastAPI\napp = FastAPI()",
        backend_models_py="from pydantic import BaseModel\nclass Watch(BaseModel): name: str",
        frontend_app_tsx="export default function App() { return <div>App</div>; }",
        frontend_api_client_ts="export async function getWatches() { return []; }",
    )
    mock_devops = DevopsSpecification(
        cloud_target="gcp",
        terraform_main_tf='resource "google_cloud_run_service" "api" {}',
        terraform_variables_tf='variable "project_id" {}',
        docker_compose_yml="version: '3.8'\nservices:\n  db:\n    image: postgres:16",
        ci_cd_workflow_yml="name: Deploy\non: [push]",
    )
    mock_qa = QaSpecification(
        test_suite_code="def test_health(): assert True",
        security_verdict="All guardrails pass",
        passed_preflight=True,
    )

    class ITMockProvider(MockProvider):
        def structured(self, prompt: str, response_model: Any, **kwargs: Any) -> Any:  # type: ignore[override]
            if response_model == ProductProposal:
                return mock_proposal
            if response_model == SolutionBlueprint:
                return mock_solution
            if response_model == DataArchitecture:
                return mock_data
            if response_model == UiSpecification:
                return mock_ui
            if response_model == FullStackSpecification:
                return mock_fullstack
            if response_model == DevopsSpecification:
                return mock_devops
            if response_model == QaSpecification:
                return mock_qa
            return super().structured(prompt, response_model, **kwargs)

    team = NexusITTeam(provider=ITMockProvider())
    out_dir = tmp_path / "delivered"
    out_dir.mkdir(parents=True, exist_ok=True)

    project = team.build_from_idea(
        "I want a watch tracking app", target_cloud="gcp", output_dir=out_dir
    )

    assert project.proposal.app_name == "watchhub"
    assert project.solution.cloud_provider == "gcp"
    assert project.output_path is not None

    app_path = Path(project.output_path)
    assert (app_path / "docs" / "PROPOSAL.md").exists()
    assert (app_path / "docs" / "ARCHITECTURE.md").exists()
    assert (app_path / "docs" / "DATA_ARCHITECTURE.md").exists()
    assert (app_path / "frontend" / "src" / "App.tsx").exists()
    assert (app_path / "frontend" / "package.json").exists()
    assert (app_path / "backend" / "src" / "main.py").exists()
    assert (app_path / "backend" / "tests" / "test_api.py").exists()
    assert (app_path / "infra" / "terraform" / "main.tf").exists()
    assert (app_path / "docker-compose.yml").exists()
