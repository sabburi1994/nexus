"""Nexus Maintenance: Closed-loop self-healing orchestrator for autonomous bug fixing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from nexus.dashboard.telemetry import AgentEvent, EventType, event_bus
from nexus.maintenance.healer import AutonomousHealer, DiagnosisResult

if TYPE_CHECKING:
    from nexus.providers.base import BaseModelProvider
    from nexus.teams.it_pack.ba import ProductProposal
    from nexus.teams.it_pack.fullstack import FullStackEngineerAgent, FullStackSpecification
    from nexus.teams.it_pack.qa import QaEngineerAgent, QaSpecification
    from nexus.teams.it_pack.solution_architect import SolutionBlueprint

logger = logging.getLogger("nexus.maintenance.healing_loop")


class HealingAttempt(BaseModel):
    """Record of a single self-healing iteration."""

    attempt_number: int
    diagnosis: DiagnosisResult
    fixed_backend_snippet: str
    passed_preflight_after_fix: bool
    details: str = ""


class SelfHealingReport(BaseModel):
    """Complete summary and history of the self-healing loop."""

    was_healing_required: bool = False
    attempts: list[HealingAttempt] = Field(default_factory=list)
    resolved: bool = True
    total_cycles: int = 0
    final_verdict: str = "PASS"


class ClosedLoopHealer:
    """
    Orchestrates the closed-loop feedback cycle between QA and Full-Stack Engineer:
    QA fails preflight -> Healer diagnoses error -> Full-Stack generates patch -> QA re-tests.
    Guarantees bounded execution to protect token budgets.
    """

    def __init__(
        self,
        provider: BaseModelProvider,
        max_healing_cycles: int = 3,
    ) -> None:
        self.provider = provider
        self.max_healing_cycles = max_healing_cycles
        self.healer = AutonomousHealer(provider)

    def run_healing_loop(
        self,
        proposal: ProductProposal,
        solution: SolutionBlueprint,
        fullstack: FullStackSpecification,
        qa: QaSpecification,
        fullstack_agent: FullStackEngineerAgent,
        qa_agent: QaEngineerAgent,
    ) -> tuple[FullStackSpecification, QaSpecification, SelfHealingReport]:
        """
        Evaluate QA preflight status and autonomously heal code until green or max cycles reached.
        """
        report = SelfHealingReport()

        if qa.passed_preflight:
            logger.info("Preflight clearance already achieved; no healing required.")
            report.was_healing_required = False
            report.resolved = True
            return fullstack, qa, report

        report.was_healing_required = True
        logger.warning("QA Preflight clearance failed. Initiating Closed-Loop Self-Healing...")

        current_fullstack = fullstack
        current_qa = qa

        for cycle in range(1, self.max_healing_cycles + 1):
            report.total_cycles = cycle
            event_bus.emit(
                AgentEvent(
                    EventType.AGENT_STARTED,
                    "Self-Healing Orchestrator",
                    f"Healing cycle {cycle}/{self.max_healing_cycles}: Diagnosing failure and synthesizing patch...",
                )
            )

            # 1. Diagnose failure from QA report
            error_msg = f"QA preflight security or test failure: {current_qa.security_verdict}"
            stack_trace = f"Failing test suite:\n{current_qa.test_suite_code[:500]}"
            diagnosis = self.healer.diagnose_failure(
                error_message=error_msg,
                stack_trace=stack_trace,
                context_snippet=current_fullstack.backend_main_py[:1000],
            )

            # 2. Instruct Full-Stack Engineer to apply patch
            patched_fullstack = fullstack_agent.heal_application(
                proposal=proposal,
                current_spec=current_fullstack,
                diagnosis=diagnosis,
            )

            # 3. Re-verify with QA Engineer
            re_verified_qa = qa_agent.verify_and_test(
                proposal=proposal,
                solution=solution,
                fullstack=patched_fullstack,
            )

            attempt = HealingAttempt(
                attempt_number=cycle,
                diagnosis=diagnosis,
                fixed_backend_snippet=patched_fullstack.backend_main_py[:150],
                passed_preflight_after_fix=re_verified_qa.passed_preflight,
                details=f"Cycle {cycle}: Verdict = {'PASS' if re_verified_qa.passed_preflight else 'FAIL'}",
            )
            report.attempts.append(attempt)

            current_fullstack = patched_fullstack
            current_qa = re_verified_qa

            if re_verified_qa.passed_preflight:
                logger.info("Closed-Loop Self-Healing SUCCESS in cycle %d!", cycle)
                event_bus.emit(
                    AgentEvent(
                        EventType.STEP_COMPLETED,
                        "Self-Healing Orchestrator",
                        f"Resolved preflight failure in cycle {cycle}. 100% QA Clearance achieved.",
                    )
                )
                report.resolved = True
                report.final_verdict = "PASS"
                break
        else:
            logger.error("Closed-Loop Self-Healing exceeded max cycles (%d).", self.max_healing_cycles)
            report.resolved = False
            report.final_verdict = "FAIL_MAX_CYCLES_EXCEEDED"

        return current_fullstack, current_qa, report
