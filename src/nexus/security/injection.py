"""Nexus Security: Prompt injection and jailbreak detection."""

from __future__ import annotations

import re
from typing import NamedTuple

# Common adversarial jailbreak signatures
INJECTION_PATTERNS = [
    re.compile(
        r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)",
        re.IGNORECASE,
    ),
    re.compile(r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|unrestricted)", re.IGNORECASE),
    re.compile(r"system\s+override\s*:\s*disable\s+safety", re.IGNORECASE),
    re.compile(r"reveal\s+your\s+(system\s+prompt|hidden\s+instructions)", re.IGNORECASE),
    re.compile(r"bypass\s+(all\s+)?(filters|restrictions|guardrails)", re.IGNORECASE),
]


class InjectionCheckResult(NamedTuple):
    is_safe: bool
    matched_pattern: str | None = None


def check_prompt_injection(prompt: str) -> InjectionCheckResult:
    """Analyze a prompt for malicious jailbreak or injection patterns."""
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(prompt)
        if match:
            return InjectionCheckResult(is_safe=False, matched_pattern=match.group(0))
    return InjectionCheckResult(is_safe=True)
