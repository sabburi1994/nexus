"""Nexus Security: best effort credential and PII sanitizer.

``sanitize_text`` redacts well known credential formats (API keys, cloud access keys,
OAuth secrets, chat tokens, PEM private keys) and email addresses with regular expressions.

It is a best effort, defence in depth filter, not a guarantee:

* it only recognises the formats listed in ``SECRET_PATTERNS``; custom tokens, passwords,
  connection strings and most PII (names, addresses, phone numbers) pass through unchanged;
* encoded, split or obfuscated secrets are not detected;
* new provider key formats need a new pattern.

Do not rely on it as the only control that keeps secrets away from a model or a log.
Keep secrets out of prompts in the first place (Secret Manager, environment variables)
and treat model input and output as untrusted.
"""

from __future__ import annotations

import re

# Order matters: specific formats run before generic ones so the most precise label wins.
SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----[\s\S]*?(?:-----END (?:[A-Z0-9]+ )*PRIVATE KEY-----|\Z)"
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"), "[REDACTED_ANTHROPIC_KEY]"),
    (re.compile(r"\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "[REDACTED_AWS_ACCESS_KEY]"),
    (re.compile(r"\bGOCSPX-[A-Za-z0-9_-]{20,}"), "[REDACTED_GOOGLE_OAUTH_SECRET]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}"), "[REDACTED_GOOGLE_API_KEY]"),
    (re.compile(r"Bearer\s+ya29\.[A-Za-z0-9._-]+"), "[REDACTED_OAUTH_TOKEN]"),
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}\b"),
        "[REDACTED_EMAIL]",
    ),
]

# Every marker ``sanitize_text`` can emit, for callers that count redactions.
REDACTION_MARKERS: tuple[str, ...] = tuple(dict.fromkeys(label for _, label in SECRET_PATTERNS))


def sanitize_text(text: str) -> str:
    """Best effort redaction of known credential formats and email addresses.

    See the module docstring for what this does not catch.
    """
    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def count_redactions(text: str) -> int:
    """Count redaction markers in already sanitized text."""
    return sum(text.count(marker) for marker in REDACTION_MARKERS)
