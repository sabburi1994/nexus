"""Nexus IT Pack: DevOps Engineer Agent."""

from __future__ import annotations

from pydantic import BaseModel, Field

from nexus.providers.base import BaseModelProvider
from nexus.teams.it_pack.ba import ProductProposal
from nexus.teams.it_pack.solution_architect import SolutionBlueprint


class DevopsSpecification(BaseModel):
    """Infrastructure as Code (Terraform) and deployment configurations."""

    cloud_target: str = Field(description="Cloud target: gcp, aws, or local")
    terraform_main_tf: str = Field(description="Complete, executable Terraform main.tf file")
    terraform_variables_tf: str = Field(description="Terraform variables.tf file")
    docker_compose_yml: str = Field(description="Local development docker-compose.yml file")
    ci_cd_workflow_yml: str = Field(description="GitHub Actions CI/CD deployment workflow")


class DevopsEngineerAgent:
    """
    DevOps Engineer Agent in the Nexus IT Pack.
    Builds customized Terraform (IaC) code, Docker configs, and CI/CD pipelines matching the architectural need.
    """

    def __init__(self, provider: BaseModelProvider) -> None:
        self.provider = provider

    def build_infrastructure(self, proposal: ProductProposal, solution: SolutionBlueprint) -> DevopsSpecification:
        """Generate Terraform IaC and deployment artifacts for the target cloud."""
        prompt = f"""You are a Senior DevOps & Cloud Infrastructure Engineer.
Design the Infrastructure as Code (Terraform) and container configs for:
App: {proposal.title} ({proposal.app_name})
Cloud Target: {solution.cloud_provider}
Compute Pattern: {solution.compute_pattern}
Required Services: {", ".join(solution.integration_services)}

Generate:
1. `terraform_main_tf`: Complete Terraform configuration provisioning the compute environment, service accounts with least privilege (e.g. roles/aiplatform.user for Gemini 3.8 on GCP), and secrets.
2. `terraform_variables_tf`: Clean variable definitions.
3. `docker_compose_yml`: Local multi-container compose file running PostgreSQL and the app.
4. `ci_cd_workflow_yml`: Complete GitHub Actions CI/CD workflow with explicit lifecycle stages:
   - Stage 1 [Lint & Static Analysis]: Ruff and syntax validation
   - Stage 2 [Automated Test Suite]: Pytest execution with strict pass gates
   - Stage 3 [Build & Push]: Container packaging and tagging
   - Stage 4 [Deployment & Health Probe]: Cloud deployment with post-deploy HTTP /health probe green flag validation.
"""
        system = (
            "You are an elite DevOps Engineer specializing in clean Terraform (IaC) and reliable cloud deployments."
        )
        return self.provider.structured(prompt, DevopsSpecification, system_instruction=system)
