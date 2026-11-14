"""Nexus Security: best effort prompt injection and jailbreak detection.

``check_prompt_injection`` matches a short list of well known jailbreak phrasings with regular
expressions. It is a cheap first filter, not a defence: paraphrases, other languages, encodings,
indirect injection through retrieved documents or tool output, and multi turn attacks all pass.
Treat every model input and output as untrusted, give agents least privilege tools, and require
human approval for critical actions (see ``GuardrailManager``).
"""

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
    """Best effort check of a prompt against known jailbreak phrasings.

    ``is_safe=True`` only means no known pattern matched; it does not mean the prompt is safe.
    """
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(prompt)
        if match:
            return InjectionCheckResult(is_safe=False, matched_pattern=match.group(0))
    return InjectionCheckResult(is_safe=True)
