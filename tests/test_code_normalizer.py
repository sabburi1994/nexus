"""Tests for the model output code normalizer used when the squad writes generated files."""

from __future__ import annotations

import ast

import pytest

from nexus.teams.it_pack.code_normalizer import normalize_python, normalize_source
from nexus.teams.it_pack.team import NexusITTeam

MAIN = '''"""Service."""
from nexus.api import create_nexus_app

from models import Item

app, db = create_nexus_app(title="Svc")


@app.get("/items")
def items() -> list[str]:
    return ["a\\nb"]
'''

TESTS = """from fastapi.testclient import TestClient

from main import app


def test_health() -> None:
    assert TestClient(app).get("/health").status_code == 200
"""

FENCE = "`" * 3


@pytest.mark.parametrize("code", [MAIN, TESTS])
def test_clean_code_is_unchanged(code: str) -> None:
    assert normalize_python(code) == code


@pytest.mark.parametrize("code", [MAIN, TESTS])
def test_normalization_is_idempotent(code: str) -> None:
    once = normalize_python(f"{FENCE}python\n{code}{FENCE}")
    assert normalize_python(once) == once


@pytest.mark.parametrize(
    "dirty",
    [
        f"{FENCE}python\n{MAIN}{FENCE}",
        f"{FENCE}\n{MAIN}{FENCE}\n",
        f"Here is the complete file:\n\n{FENCE}python\n{MAIN}{FENCE}\n\nThis implements the endpoints.",
        f"{FENCE}python\n{MAIN}",  # opening fence only
        f"{MAIN}{FENCE}\n",  # closing fence only
        "﻿" + MAIN,
        MAIN.replace("\n", "\r\n"),
        "python\n" + MAIN,
        "Sure! Below is main.py.\n" + MAIN + "\nLet me know if you need changes.",
    ],
)
def test_wrapped_code_is_recovered(dirty: str) -> None:
    assert normalize_python(dirty) == MAIN


def test_largest_fenced_block_wins() -> None:
    dirty = f"Usage:\n{FENCE}bash\nuvicorn main:app\n{FENCE}\nFile:\n{FENCE}python\n{MAIN}{FENCE}\n"
    assert normalize_python(dirty) == MAIN


def test_double_escaped_file_is_unescaped() -> None:
    escaped = TESTS.replace("\n", "\\n")
    assert normalize_python(escaped) == TESTS


def test_string_escapes_in_valid_code_are_kept() -> None:
    # The "\n" inside the string literal must not be turned into a real newline.
    assert '"a\\nb"' in normalize_python(MAIN)


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("from backend.src.main import app", "from main import app"),
        ("from src.main import app", "from main import app"),
        ("from app.main import app", "from main import app"),
        ("from api.main import app", "from main import app"),
        ("from .models import Item", "from models import Item"),
        ("from ..backend_models import Item", "from backend_models import Item"),
        ("from backend import main", "import main"),
        ("from app.src import models", "import models"),
    ],
)
def test_local_imports_follow_the_flat_layout(line: str, expected: str) -> None:
    out = normalize_python(f"{line}\n\nx = 1\n")
    assert out.splitlines()[0] == expected


def test_third_party_imports_are_not_rewritten() -> None:
    code = "from fastapi.applications import FastAPI\nfrom starlette.main import thing\n\nx = (FastAPI, thing)\n"
    assert normalize_python(code) == code


def test_missing_well_known_imports_are_added_after_docstring_and_future() -> None:
    code = '"""Tests."""\nfrom __future__ import annotations\n\nfrom main import app\n\n\ndef test_x() -> None:\n    with pytest.raises(ValueError):\n        TestClient(app)\n'
    out = normalize_python(code)
    tree = ast.parse(out)
    imported = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
    assert {"pytest", "TestClient"} <= imported
    lines = out.splitlines()
    assert lines[0] == '"""Tests."""'
    assert lines[1] == "from __future__ import annotations"


def test_locally_defined_names_get_no_import() -> None:
    code = "class TestClient:\n    pass\n\n\ndef status() -> int:\n    return 1\n\n\nx = TestClient(), status()\n"
    assert normalize_python(code) == code


def test_redundant_base_mixin_is_removed() -> None:
    out = normalize_python("from nexus.db import Base, NexusEntity\n\n\nclass Item(Base, NexusEntity):\n    pass\n")
    assert "class Item(NexusEntity):" in out


def test_unrecoverable_code_is_returned_cleaned_not_dropped() -> None:
    out = normalize_python(f"{FENCE}python\ndef broken(:\n{FENCE}")
    assert out == "def broken(:\n"


def test_code_lines_are_never_dropped_to_make_a_file_parse() -> None:
    code = "x = 1\ndef broken(:\n"
    assert normalize_python(code) == code


def test_fence_inside_a_docstring_is_preserved() -> None:
    code = f'"""Example:\n\n{FENCE}python\nx = 1\n{FENCE}\n"""\n\ny = 2\n'
    assert normalize_python(code) == code


def test_source_normalizer_strips_edge_fences_only() -> None:
    tsx = "export const md = `\n" + FENCE + "js\nx\n" + FENCE + "\n`;\nexport default md;\n"
    for _ in range(3):
        tsx = "// padding line\n" + tsx
    assert normalize_source(tsx) == tsx
    assert normalize_source(f"{FENCE}tsx\nexport const a = 1;\n{FENCE}") == "export const a = 1;\n"
    assert normalize_source('﻿resource "x" "y" {}\r\n') == 'resource "x" "y" {}\n'
    assert normalize_source(None) == ""
    assert normalize_source("") == ""


def test_team_sanitizer_uses_the_normalizer() -> None:
    assert NexusITTeam._sanitize_python(f"{FENCE}python\n{MAIN}{FENCE}") == MAIN
