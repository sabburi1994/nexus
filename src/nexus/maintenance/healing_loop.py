"""Nexus Maintenance: Closed-loop self-healing orchestrator for autonomous bug fixing."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from nexus.dashboard.telemetry import AgentEvent, EventType, event_bus
from nexus.maintenance.healer import AutonomousHealer, DiagnosisResult
from nexus.qa.runner import TestRunResult

if TYPE_CHECKING:
    from nexus.providers.base import BaseModelProvider
    from nexus.teams.it_pack.ba import ProductProposal
    from nexus.teams.it_pack.fullstack import FullStackEngineerAgent, FullStackSpecification
    from nexus.teams.it_pack.qa import QaEngineerAgent, QaSpecification
    from nexus.teams.it_pack.solution_architect import SolutionBlueprint

logger = logging.getLogger("nexus.maintenance.healing_loop")

TestRunner = Callable[["FullStackSpecification", "QaSpecification"], TestRunResult]
"""Writes the given code to a workspace, runs its generated pytest suite and returns the result."""


def qa_gate_passed(qa: QaSpecification, test_run: TestRunResult | None) -> bool:
    """QA gate: the generated tests must pass when they were run, and QA's own review must pass.

    Without a real test run (no workspace on disk, or execution disabled) only QA's self
    reported ``passed_preflight`` is available.
    """
    if test_run is not None and not test_run.passed:
        return False
    return qa.passed_preflight


class HealingAttempt(BaseModel):
    """Record of a single self-healing iteration."""

    attempt_number: int
    diagnosis: DiagnosisResult
    fixed_backend_snippet: str
    passed_preflight_after_fix: bool = Field(description="QA gate after the patch (real test run included)")
    details: str = ""
    test_run: TestRunResult | None = None


class SelfHealingReport(BaseModel):
    """Complete summary and history of the self-healing loop."""

    was_healing_required: bool = False
    attempts: list[HealingAttempt] = Field(default_factory=list)
    resolved: bool = True
    total_cycles: int = 0
    final_verdict: str = "PASS"
    tests_executed: bool = Field(default=False, description="True if the generated suite was run for real")
    initial_test_run: TestRunResult | None = None
    final_test_run: TestRunResult | None = None


class ClosedLoopHealer:
    """
    Orchestrates the closed-loop feedback cycle between QA and Full-Stack Engineer:
    QA gate fails -> Healer diagnoses the failure -> Full-Stack generates patch -> QA re-tests.

    With a ``test_runner`` the gate is a real pytest run of the generated suite and the
    diagnosis is fed the actual pytest output. Without one it falls back to QA's self
    reported ``passed_preflight``. Execution is bounded by ``max_healing_cycles``.
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
        test_runner: TestRunner | None = None,
        initial_test_run: TestRunResult | None = None,
    ) -> tuple[FullStackSpecification, QaSpecification, SelfHealingReport]:
        """
        Check the QA gate and heal the code until it passes or max cycles are reached.

        ``initial_test_run`` avoids running the suite twice when the caller already ran it.
        """
        report = SelfHealingReport(tests_executed=test_runner is not None or initial_test_run is not None)

        test_run = initial_test_run
        if test_run is None and test_runner is not None:
            test_run = test_runner(fullstack, qa)
        report.initial_test_run = test_run
        report.final_test_run = test_run

        if qa_gate_passed(qa, test_run):
            logger.info("QA gate already passed; no healing required.")
            report.was_healing_required = False
            report.resolved = True
            return fullstack, qa, report

        report.was_healing_required = True
        logger.warning(
            "QA gate failed (%s). Initiating Closed-Loop Self-Healing...",
            test_run.summary if test_run is not None else "self reported preflight",
        )

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

            # 1. Diagnose the failure: real pytest output when the suite was run.
            error_msg, stack_trace = self._failure_context(current_qa, test_run)
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

            # 3. Re-verify with QA Engineer, then run the (regenerated) suite for real.
            re_verified_qa = qa_agent.verify_and_test(
                proposal=proposal,
                solution=solution,
                fullstack=patched_fullstack,
            )
            if test_runner is not None:
                test_run = test_runner(patched_fullstack, re_verified_qa)
            passed = qa_gate_passed(re_verified_qa, test_run)

            details = f"Cycle {cycle}: Verdict = {'PASS' if passed else 'FAIL'}"
            if test_run is not None:
                details += f" ({test_run.summary})"
            attempt = HealingAttempt(
                attempt_number=cycle,
                diagnosis=diagnosis,
                fixed_backend_snippet=patched_fullstack.backend_main_py[:150],
                passed_preflight_after_fix=passed,
                details=details,
                test_run=test_run,
            )
            report.attempts.append(attempt)
            report.final_test_run = test_run

            current_fullstack = patched_fullstack
            current_qa = re_verified_qa

            if passed:
                logger.info("Closed-Loop Self-Healing SUCCESS in cycle %d!", cycle)
                event_bus.emit(
                    AgentEvent(
                        EventType.STEP_COMPLETED,
                        "Self-Healing Orchestrator",
                        f"Resolved QA failure in cycle {cycle}."
                        + (f" {test_run.summary}." if test_run is not None else ""),
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

    @staticmethod
    def _failure_context(qa: QaSpecification, test_run: TestRunResult | None) -> tuple[str, str]:
        """Error message and trace for the diagnosis prompt."""
        if test_run is not None and not test_run.passed:
            return (
                f"Generated pytest suite failed: {test_run.summary}",
                f"pytest output (tail):\n{test_run.output_tail[-3000:]}\n\n"
                f"Generated test suite (head):\n{qa.test_suite_code[:1500]}",
            )
        return (
            f"QA preflight security or test failure: {qa.security_verdict}",
            f"Failing test suite:\n{qa.test_suite_code[:500]}",
        )
