"""Tests for the best effort secret sanitizer key formats.

Fake credentials are assembled from fragments at runtime so secret scanners
(gitleaks in the pre-commit hook) do not flag this file.
"""

from __future__ import annotations

import pytest

from nexus.security.sanitizer import REDACTION_MARKERS, count_redactions, sanitize_text

FAKE_ANTHROPIC = "sk-" + "ant-" + "api03-" + "a1B2c3D4e5F6g7H8i9J0" + "kLmNoPqRsTuV_wx-yz"
FAKE_OPENAI_PROJECT = "sk-" + "proj-" + "Zz9Yy8Xx7Ww6Vv5Uu4Tt3Ss2"
FAKE_AWS = "AKIA" + "QWERTYUIOPASDF12"
FAKE_AWS_TEMP = "ASIA" + "ZXCVBNMLKJHGFD34"
FAKE_GOOGLE_OAUTH = "GOCSPX-" + "Ab12Cd34Ef56Gh78Ij90Kl12Mn34"
FAKE_SLACK_BOT = "xoxb-" + "123456789012-1234567890123-" + "AbCdEfGhIjKlMnOpQrStUvWx"
FAKE_SLACK_USER = "xoxp-" + "123456789012-123456789012-" + "aBcDeFgHiJ"
FAKE_GITHUB = "ghp_" + "A" * 36
FAKE_PEM = (
    "-----BEGIN " + "RSA PRIVATE KEY-----\n"
    "MIIEowIBAAKCAQEAfakefakefakefakefakefakefake\n"
    "bm90IGEgcmVhbCBrZXkgYXQgYWxs\n"
    "-----END " + "RSA PRIVATE KEY-----"
)
FAKE_PEM_PKCS8 = "-----BEGIN " + "PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAAfake\n-----END " + "PRIVATE KEY-----"


@pytest.mark.parametrize(
    ("secret", "marker"),
    [
        (FAKE_ANTHROPIC, "[REDACTED_ANTHROPIC_KEY]"),
        (FAKE_OPENAI_PROJECT, "[REDACTED_API_KEY]"),
        (FAKE_AWS, "[REDACTED_AWS_ACCESS_KEY]"),
        (FAKE_AWS_TEMP, "[REDACTED_AWS_ACCESS_KEY]"),
        (FAKE_GOOGLE_OAUTH, "[REDACTED_GOOGLE_OAUTH_SECRET]"),
        (FAKE_SLACK_BOT, "[REDACTED_SLACK_TOKEN]"),
        (FAKE_SLACK_USER, "[REDACTED_SLACK_TOKEN]"),
        (FAKE_GITHUB, "[REDACTED_GITHUB_TOKEN]"),
        (FAKE_PEM, "[REDACTED_PRIVATE_KEY]"),
        (FAKE_PEM_PKCS8, "[REDACTED_PRIVATE_KEY]"),
    ],
)
def test_sanitizer_redacts_key_format(secret: str, marker: str) -> None:
    text = f"config before {secret} config after"
    clean = sanitize_text(text)
    assert secret not in clean
    assert marker in clean
    assert clean.startswith("config before ")
    assert clean.endswith(" config after")
    assert marker in REDACTION_MARKERS
    assert count_redactions(clean) == 1


def test_private_key_block_body_fully_removed() -> None:
    clean = sanitize_text(f"key:\n{FAKE_PEM}\nend")
    assert "MIIEowIBAAKCAQEA" not in clean
    assert "bm90IGEgcmVhbCBrZXk" not in clean
    assert clean == "key:\n[REDACTED_PRIVATE_KEY]\nend"


def test_truncated_private_key_block_is_redacted_to_end() -> None:
    truncated = "-----BEGIN " + "EC PRIVATE KEY-----\nMHcCAQEEIfakefake"
    clean = sanitize_text(f"pasted: {truncated}")
    assert "MHcCAQEEIfakefake" not in clean
    assert "[REDACTED_PRIVATE_KEY]" in clean


def test_anthropic_key_gets_specific_label() -> None:
    clean = sanitize_text(FAKE_ANTHROPIC)
    assert clean == "[REDACTED_ANTHROPIC_KEY]"


def test_sanitizer_leaves_ordinary_text_alone() -> None:
    text = "Ask the AKIA team about task-ant-farm and xoxo hugs; ghp is fine."
    assert sanitize_text(text) == text
    assert count_redactions(text) == 0
