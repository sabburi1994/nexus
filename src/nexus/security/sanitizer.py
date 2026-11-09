"""Nexus Security: Credential and PII Sanitizer."""

from __future__ import annotations

import re

# Redaction patterns for secrets
SECRET_PATTERNS = [
    (re.compile(r"(sk-[a-zA-Z0-9]{20,})"), "[REDACTED_API_KEY]"),
    (re.compile(r"(ghp_[a-zA-Z0-9]{36})"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"(AIza[0-9A-Za-z-_]{35})"), "[REDACTED_GOOGLE_API_KEY]"),
    (re.compile(r"(Bearer\s+ya29\.[a-zA-Z0-9_-]+)"), "[REDACTED_OAUTH_TOKEN]"),
    (
        re.compile(r"(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b)"),
        "[REDACTED_EMAIL]",
    ),
]


def sanitize_text(text: str) -> str:
    """Scrub sensitive credentials, tokens, and PII from text before model ingestion."""
    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized
