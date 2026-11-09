"""Nexus IT Pack: DevOps Engineer Agent."""

from __future__ import annotations

from pydantic import BaseModel, Field

from nexus.providers.base import BaseModelProvider
from nexus.teams.it_pack.ba import ProductProposal
from nexus.teams.it_pack.solution_architect import SolutionBlueprint


class DevopsSpecification(BaseModel):
    """Infrastructure as Code (Terraform) and deployment configurations."""

    cloud_target: str = Field(description="Cloud target: gcp, aws, or local")
    terraform_main_tf: str = Field(
        description="Complete, executable Terraform main.tf file using modern serverless containers"
    )
    terraform_variables_tf: str = Field(description="Terraform variables.tf file")
    docker_compose_yml: str = Field(description="Local development docker-compose.yml file")
    ci_cd_workflow_yml: str = Field(description="Terraform automated deployment script / configuration")


class DevopsEngineerAgent:
    """
    DevOps Engineer Agent in the Nexus IT Pack.
    Builds customized Terraform (IaC) code and modern serverless container configs matching architectural requirements.
    """

    def __init__(self, provider: BaseModelProvider) -> None:
        self.provider = provider

    def build_infrastructure(self, proposal: ProductProposal, solution: SolutionBlueprint) -> DevopsSpecification:
        """Generate Terraform IaC and deployment artifacts for the target cloud."""
        prompt = f"""You are a Senior DevOps & Cloud Infrastructure Engineer.
Design the Infrastructure as Code (Terraform) and container configs for:
App: {proposal.title} ({proposal.app_name})
Cloud Target: {solution.cloud_provider}
Compute Pattern: Standardize on Google Cloud Run v2 (Serverless, auto-scaling 0..N). Do NOT use legacy Compute Engine VMs.
Required Services: {", ".join(solution.integration_services)}

Generate:
1. `terraform_main_tf`: Complete Terraform configuration provisioning:
   - Google Cloud Run v2 service with serverless autoscaling (min 0, max 5)
   - Google Artifact Registry repository
   - Least-privilege IAM service account with `roles/aiplatform.user` (Vertex AI Gemini 3.8 Flash)
   - Secret Manager bindings and public invoker permissions (`roles/run.invoker`)
2. `terraform_variables_tf`: Clean variable definitions (project_id, region, service_name, image_tag).
3. `docker_compose_yml`: Local multi-container compose file running PostgreSQL and the app.
4. `ci_cd_workflow_yml`: Shell / PowerShell automated deployment script executing `terraform init` and `terraform apply`.
"""
        system = "You are an elite DevOps Engineer specializing in clean Terraform (IaC) and modern serverless cloud infrastructure."
        return self.provider.structured(prompt, DevopsSpecification, system_instruction=system)
