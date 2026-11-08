"""Nexus IT Pack: Solution Architect Agent."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field
from nexus.providers.base import BaseModelProvider
from nexus.teams.it_pack.ba import ProductProposal


class SolutionBlueprint(BaseModel):
    """Holistic system architecture and cloud infrastructure strategy."""
    cloud_provider: Literal["gcp", "aws", "local"] = Field(
        description="Recommended cloud runtime target ('gcp', 'aws', or 'local')",
        default="gcp",
    )
    compute_pattern: str = Field(description="e.g. Cloud Run serverless container, or Compute VM")
    system_topology: str = Field(description="System topology overview describing communication between frontend, backend, DB, and AI")
    non_functional_requirements: list[str] = Field(description="Scalability, latency, security, and availability guidelines")
    integration_services: list[str] = Field(description="Cloud services needed: e.g. Vertex AI, Secret Manager, Cloud SQL")


class SolutionArchitectAgent:
    """
    Solution Architect Agent in the Nexus IT Pack.
    Evaluates proposals and designs the holistic system topology and cloud infrastructure strategy.
    """

    def __init__(self, provider: BaseModelProvider) -> None:
        self.provider = provider

    def design_solution(self, proposal: ProductProposal, target_cloud: str = "gcp") -> SolutionBlueprint:
        """Formulate complete system solution blueprint."""
        prompt = f"""You are a Principal Solution Architect.
Review the following product proposal:
App: {proposal.title} ({proposal.app_name})
Tagline: {proposal.tagline}
Core Features: {', '.join(proposal.core_features)}
User Stories: {', '.join(proposal.user_stories)}
Preferred Cloud: {target_cloud}

Design the complete solution architecture:
1. Select appropriate cloud services (Vertex AI for Gemini 3.8, Cloud Run/Compute, PostgreSQL).
2. Define the compute pattern.
3. Detail the communication topology between frontend, backend, data layer, and external APIs.
4. Establish non-functional requirements (high availability, latency targets, least-privilege security).
"""
        system = "You are a pragmatic, battle-tested Principal Solution Architect."
        return self.provider.structured(prompt, SolutionBlueprint, system_instruction=system)
