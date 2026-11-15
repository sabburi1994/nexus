"""Turn model returned code fields into clean source files before they are written to disk.

Structured model output often carries code that is correct but not a clean file: wrapped in
markdown fences, surrounded by explanatory prose, double escaped (literal ``\\n``), prefixed with a
language tag or a BOM, using Windows line endings, importing the app through a package path the
generated layout does not have (``from backend.src.main import app``), or forgetting a well known
import (``TestClient``). Each of those breaks an otherwise working generated app.

Python repairs are only kept when the result parses (``ast.parse``) and the input did not, or when
the repair is purely textual (BOM, line endings, fences). Valid code is never made invalid.
``benchmarks/bench_output_defects.py`` measures how many defect types are absorbed.
"""

from __future__ import annotations

import ast
import builtins
import json
import re

_BOM = "\N{ZERO WIDTH NO-BREAK SPACE}"
_PROSE_LINE = re.compile(r"^[A-Z][^=(){}\[\]<>#@`]*[.:!?]?$")
_CODE_START = re.compile(r"^(?:import|from|def|class|async|return|if|for|while|with|try|raise|assert|print)\b")
_FENCE_BLOCK = re.compile(r"```[ \t]*([A-Za-z0-9_+.-]*)[ \t]*\r?\n(.*?)(?:\r?\n)?```", re.S)
_LANG_TAGS = {"python", "python3", "py", "typescript", "ts", "tsx", "javascript", "js", "jsx", "hcl", "terraform"}
_LOCAL_MODULES = ("main", "models", "backend_models")
# Package prefixes a model may invent for the flat generated layout (backend/src/main.py).
_LOCAL_PREFIX = r"(?:\.+|(?:(?:backend|app|api|src|server|service)\.)+)"
_LOCAL_IMPORT = re.compile(
    rf"^(?P<indent>[ \t]*)from[ \t]+{_LOCAL_PREFIX}(?P<mod>{'|'.join(_LOCAL_MODULES)})[ \t]+import[ \t]",
    re.M,
)
_BARE_LOCAL_PKG_IMPORT = re.compile(
    rf"^(?P<indent>[ \t]*)from[ \t]+(?:backend|app|api|src|server|service)(?:\.(?:src|app))?[ \t]+import[ \t]+(?P<mod>{'|'.join(_LOCAL_MODULES)})\b",
    re.M,
)

# Names models use without importing, and the import that provides them.
KNOWN_IMPORTS: dict[str, str] = {
    "TestClient": "from fastapi.testclient import TestClient",
    "pytest": "import pytest",
    "FastAPI": "from fastapi import FastAPI",
    "HTTPException": "from fastapi import HTTPException",
    "Depends": "from fastapi import Depends",
    "Query": "from fastapi import Query",
    "status": "from fastapi import status",
    "BaseModel": "from pydantic import BaseModel",
    "Field": "from pydantic import Field",
    "create_nexus_app": "from nexus.api import create_nexus_app",
    "NexusEntity": "from nexus.db import NexusEntity",
    "Any": "from typing import Any",
    "Optional": "from typing import Optional",
    "datetime": "import datetime",
    "uuid": "import uuid",
    "os": "import os",
    "json": "import json",
}


def _parses(code: str) -> bool:
    try:
        ast.parse(code)
    except (SyntaxError, ValueError):
        return False
    return True


def _basic(code: str) -> str:
    """BOM, line endings and a leading language tag line (``python`` alone on the first line)."""
    text = code.lstrip(_BOM).replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    while lines and lines[0].strip().lower() in _LANG_TAGS:
        lines = lines[1:]
    return "\n".join(lines)


def _strip_fences(text: str) -> str:
    """Take the code out of markdown fences, including unbalanced ones."""
    blocks = [m.group(2) for m in _FENCE_BLOCK.finditer(text)]
    if blocks:
        # The largest fenced block is the file; smaller ones are usually usage snippets.
        return max(blocks, key=len)
    lines = text.split("\n")

    def is_fence(line: str) -> bool:
        return line.strip().startswith("```")

    # An opening fence is one with code after it; a fence followed only by blank lines is a closing one.
    opening = next(
        (i for i, ln in enumerate(lines) if is_fence(ln) and any(x.strip() for x in lines[i + 1 :])),
        None,
    )
    if opening is not None:
        lines = lines[opening + 1 :]
    return "\n".join(ln for ln in lines if not ln.strip().startswith("```"))


def _finish(text: str) -> str:
    text = text.strip("\n")
    return text + "\n" if text else text


def normalize_text(code: str) -> str:
    """Language independent cleanup: BOM, line endings, language tag, markdown fences at the edges."""
    text = _basic(code)
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    fence_at_edge = bool(lines) and (
        lines[0].startswith("```")
        or lines[-1].startswith("```")
        # "Here is the file:" style lead in directly followed by a fence.
        or (len(lines) > 1 and lines[1].startswith("```") and _is_prose(lines[0]))
    )
    if fence_at_edge:
        text = _basic(_strip_fences(text))
    return _finish(text)


def _unescape(code: str) -> str | None:
    """Undo a double escaped file (literal backslash n instead of newlines)."""
    if "\n" in code.strip() or "\\n" not in code:
        return None
    try:
        candidate = json.loads(f'"{code}"')
        if isinstance(candidate, str) and _parses(candidate):
            return candidate
    except ValueError:
        pass
    candidate = re.sub(r"(?<!\\)\\n", "\n", code)
    candidate = re.sub(r"(?<!\\)\\t", "\t", candidate)
    candidate = candidate.replace('\\"', '"').replace("\\'", "'")
    return _finish(candidate) if _parses(candidate) else None


def _is_prose(line: str) -> bool:
    """A natural language sentence, not code: starts with a capital, no code punctuation."""
    s = line.strip()
    return bool(_PROSE_LINE.match(s)) and not _CODE_START.match(s)


def _strip_prose(code: str) -> str | None:
    """Drop up to five leading and trailing prose lines (and blank lines) until the module parses.

    Only lines that read as sentences are dropped, so real code is never cut to make it parse.
    """
    lines = code.split("\n")

    def droppable(chunk: list[str]) -> bool:
        return all(not ln.strip() or _is_prose(ln) for ln in chunk)

    for head in range(0, min(6, len(lines))):
        if not droppable(lines[:head]):
            break
        for tail in range(0, min(6, len(lines) - head)):
            if not droppable(lines[len(lines) - tail :]):
                break
            body = "\n".join(lines[head : len(lines) - tail]).strip("\n")
            if body.strip() and _parses(body):
                return _finish(body)
    return None


def _fix_local_imports(code: str) -> str:
    """``from backend.src.main import app`` / ``from .models import X`` -> flat layout imports."""
    code = _LOCAL_IMPORT.sub(lambda m: f"{m.group('indent')}from {m.group('mod')} import ", code)
    return _BARE_LOCAL_PKG_IMPORT.sub(lambda m: f"{m.group('indent')}import {m.group('mod')}", code)


def _bound_names(tree: ast.AST) -> set[str]:
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            bound.add(node.id)
        elif isinstance(node, ast.arg):
            bound.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            bound.add(node.name)
    return bound


def _add_missing_imports(code: str) -> str:
    """Insert imports for well known names that are used but never bound."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    bound = _bound_names(tree) | set(dir(builtins))
    missing = sorted(name for name in used - bound if name in KNOWN_IMPORTS)
    if not missing:
        return code
    # Insert after a module docstring and ``from __future__`` imports.
    insert_at = 0
    body = tree.body
    idx = 0
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
        insert_at = body[0].end_lineno or 0
        idx = 1
    while idx < len(body) and isinstance(body[idx], ast.ImportFrom) and body[idx].module == "__future__":  # type: ignore[attr-defined]
        insert_at = body[idx].end_lineno or insert_at
        idx += 1
    lines = code.split("\n")
    new_imports = [KNOWN_IMPORTS[name] for name in missing]
    patched = "\n".join(lines[:insert_at] + new_imports + lines[insert_at:])
    return patched if _parses(patched) else code


def _fix_redundant_base(code: str) -> str:
    # class Foo(Base, NexusEntity) -> class Foo(NexusEntity): NexusEntity already derives from Base.
    return re.sub(r"class\s+([A-Za-z0-9_]+)\s*\(\s*Base\s*,\s*NexusEntity\s*\):", r"class \1(NexusEntity):", code)


def _fix_fstring_escapes(code: str) -> str:
    def fix(m: re.Match[str]) -> str:
        inner = m.group(1)
        if r"\"" in inner or r"\'" in inner or "{" in inner:
            return f'"{inner}"'
        return m.group(0)

    candidate = re.sub(r'f"([^"]+)"', fix, code)
    return candidate if _parses(candidate) else code


def normalize_python(code: str) -> str:
    """Return the best clean version of a model supplied Python file (see module docstring)."""
    text = _finish(_basic(code))
    if not _parses(text) and "```" in text:
        text = _finish(_basic(_strip_fences(text)))
    if not _parses(text):
        for repair in (_unescape, _strip_prose):
            candidate = repair(text)
            if candidate is not None:
                text = candidate
                break
    if not _parses(text):
        text = _fix_fstring_escapes(text)
    text = _fix_redundant_base(text)
    imports_fixed = _fix_local_imports(text)
    if _parses(imports_fixed) or not _parses(text):
        text = imports_fixed
    return _add_missing_imports(text)


def normalize_source(code: str | None) -> str:
    """Cleanup for non Python generated files (TypeScript, HCL, Dockerfile, YAML); None becomes ""."""
    return normalize_text(code) if code else ""
