"""Nexus IT Pack: DevOps Engineer Agent."""

from __future__ import annotations

from pydantic import AliasChoices, BaseModel, Field

from nexus.providers.base import BaseModelProvider
from nexus.teams.it_pack import platform_templates as tpl
from nexus.teams.it_pack.ba import ProductProposal
from nexus.teams.it_pack.solution_architect import SolutionBlueprint


class DevopsSpecification(BaseModel):
    """Deployment artifacts for a generated app.

    The model fills ``cloud_target``, ``docker_compose_yml``, ``needs_vertex_ai`` and
    ``runtime_secrets``. The Terraform files, the Dockerfile and the deploy script encode
    platform policy, so ``DevopsEngineerAgent`` renders them from fixed templates
    (``nexus.teams.it_pack.platform_templates``) and overwrites whatever the model returned.
    """

    cloud_target: str = Field(description="Cloud target: gcp, aws, or local")
    docker_compose_yml: str = Field(description="Local development docker-compose.yml file")
    needs_vertex_ai: bool = Field(
        default=False,
        description="True only if the backend calls Vertex AI / Gemini at runtime",
    )
    runtime_secrets: list[str] = Field(
        default_factory=list,
        description="Environment variable names (UPPER_SNAKE_CASE) the backend reads from Secret Manager",
    )
    terraform_main_tf: str = Field(default="", description="Rendered by Nexus from the platform template")
    terraform_variables_tf: str = Field(default="", description="Rendered by Nexus from the platform template")
    dockerfile: str = Field(default="", description="Rendered by Nexus: backend/Dockerfile")
    deploy_script_sh: str = Field(
        default="",
        validation_alias=AliasChoices("deploy_script_sh", "ci_cd_workflow_yml"),
        description="Rendered by Nexus: scripts/deploy.sh",
    )

    @property
    def ci_cd_workflow_yml(self) -> str:
        """Deprecated name of ``deploy_script_sh`` (it was never a workflow file)."""
        return self.deploy_script_sh


def render_platform_files(spec: DevopsSpecification, app_name: str) -> DevopsSpecification:
    """Return ``spec`` with Terraform, Dockerfile and deploy script rendered from the platform templates."""
    secrets = tpl.runtime_secret_env_names(spec.runtime_secrets)
    return spec.model_copy(
        update={
            "runtime_secrets": secrets,
            "terraform_main_tf": tpl.render_terraform_main(app_name, spec.needs_vertex_ai, secrets),
            "terraform_variables_tf": tpl.render_terraform_variables(app_name),
            "dockerfile": tpl.render_dockerfile(),
            "deploy_script_sh": tpl.render_deploy_script(app_name),
        }
    )


class DevopsEngineerAgent:
    """
    DevOps Engineer Agent in the Nexus IT Pack.
    Decides the app specific deployment inputs and renders the platform Terraform, Dockerfile
    and deploy script from fixed templates.
    """

    def __init__(self, provider: BaseModelProvider) -> None:
        self.provider = provider

    def build_infrastructure(self, proposal: ProductProposal, solution: SolutionBlueprint) -> DevopsSpecification:
        """Generate deployment artifacts for the target cloud."""
        prompt = f"""You are a Senior DevOps & Cloud Infrastructure Engineer.
Prepare the deployment inputs for:
App: {proposal.title} ({proposal.app_name})
Cloud Target: {solution.cloud_provider}
Required Services: {", ".join(solution.integration_services)}

Platform rules (already encoded in the Terraform template, do not restate them):
- Google Cloud Run v2, min 0 and max 2 instances, CPU allocated only during requests.
- Container image tagged with the git SHA; the container runs as a non root user on port 8080.
- Secret Manager access is granted per secret, never project wide.
- Vertex AI (`roles/aiplatform.user`) is granted only when the backend calls it.

Return:
1. `cloud_target`: the cloud target.
2. `docker_compose_yml`: local compose file running PostgreSQL and the backend (build context `./backend`, port 8080).
3. `needs_vertex_ai`: true only if the backend calls Vertex AI / Gemini at runtime.
4. `runtime_secrets`: UPPER_SNAKE_CASE names of the secrets the backend reads (for example DATABASE_PASSWORD); empty if none.
Leave `terraform_main_tf`, `terraform_variables_tf`, `dockerfile` and `deploy_script_sh` empty: Nexus renders them.
"""
        system = "You are an elite DevOps Engineer specializing in clean, least privilege serverless infrastructure."
        spec = self.provider.structured(prompt, DevopsSpecification, system_instruction=system)
        return render_platform_files(spec, proposal.app_name)
