"""Nexus Brownfield: Blast-radius-aware surgical refactoring engine."""

from __future__ import annotations

import logging
from pathlib import Path
from pydantic import BaseModel, Field

from nexus.brownfield.analyzer import AstDependencyMapper, BlastRadiusResult
from nexus.providers.base import BaseModelProvider
from nexus.providers.mock import MockProvider

logger = logging.getLogger("nexus.brownfield.refactor")


class FilePatch(BaseModel):
    """Surgical patch to be applied to a specific file."""

    file_path: str
    diff_or_content: str
    change_type: str = Field(description="'modify', 'create', or 'delete'")


class RefactorPlan(BaseModel):
    """Complete refactoring execution plan synthesized by Nexus."""

    task: str
    target_files: list[str]
    blast_radius: BlastRadiusResult
    patches: list[FilePatch]
    verification_strategy: str
    estimated_risk: str


class BrownfieldRefactorer:
    """
    Executes surgical codebase refactoring on brownfield systems:
    1. Ingests codebase and refactor requirement.
    2. Maps dependency graph and calculates blast radius.
    3. Synthesizes surgical diffs preserving existing contracts.
    4. Identifies existing regression test suites to run.
    """

    def __init__(self, root_dir: Path | str, provider: BaseModelProvider | None = None) -> None:
        self.root_dir = Path(root_dir).resolve()
        self.provider = provider or MockProvider()
        self.mapper = AstDependencyMapper(self.root_dir)

    def plan_refactor(self, task: str, primary_target: str | None = None) -> RefactorPlan:
        """Analyze impact and generate surgical refactor plan."""
        self.mapper.scan_codebase()

        # If target file not specified, search symbols matching task
        target = primary_target or "src/main.py"
        blast = self.mapper.compute_blast_radius(target)

        prompt = f"""You are a Principal Software Architect refactoring a brownfield repository.
Refactoring Goal: {task}
Primary Target File: {target}
Calculated Blast Radius:
- Direct Dependents: {", ".join(blast.direct_dependents) or "None"}
- Indirect Dependents: {", ".join(blast.indirect_dependents) or "None"}
- Affected Routes: {", ".join(blast.affected_routes) or "None"}
- Relevant Test Suites: {", ".join(blast.affected_tests) or "None"}

Synthesize a safe, surgical refactoring plan that avoids breaking downstream dependents.
"""
        system = "You are a pragmatic, master software architect specializing in zero-downtime refactoring."
        plan = self.provider.structured(prompt, RefactorPlan, system_instruction=system)
        plan.task = task
        plan.blast_radius = blast
        return plan
