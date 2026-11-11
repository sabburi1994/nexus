"""Nexus Brownfield: AST-based dependency mapping and blast radius analysis."""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("nexus.brownfield.analyzer")


class SymbolDefinition(BaseModel):
    """A declared class, function, or endpoint route."""

    name: str
    kind: str  # "class", "function", "route"
    file_path: str
    line_number: int
    route_path: str | None = None
    http_method: str | None = None


class BlastRadiusResult(BaseModel):
    """Calculated impact radius when a file or symbol is modified."""

    target: str
    risk_tier: str = Field(description="LOW, MEDIUM, or HIGH risk")
    direct_dependents: list[str] = Field(default_factory=list)
    indirect_dependents: list[str] = Field(default_factory=list)
    affected_routes: list[str] = Field(default_factory=list)
    affected_tests: list[str] = Field(default_factory=list)
    total_affected_files: int = 0


class AstDependencyMapper:
    """
    Constructs an AST dependency graph across a codebase:
    Tracks file imports, symbols, FastAPI routes, and computes change blast radius.
    """

    def __init__(self, root_dir: Path | str) -> None:
        self.root_dir = Path(root_dir).resolve()
        # file_path -> list of imported module strings
        self.imports_map: dict[str, set[str]] = {}
        # file_path -> list of symbols defined
        self.symbols_map: dict[str, list[SymbolDefinition]] = {}
        # file_path -> list of test files targeting it
        self.test_coverage_map: dict[str, list[str]] = {}

    def scan_codebase(self) -> dict[str, Any]:
        """Walk all supported source files and populate dependency graph."""
        if not self.root_dir.exists():
            raise FileNotFoundError(f"Directory {self.root_dir} does not exist.")

        py_files = list(self.root_dir.rglob("*.py"))
        for py_path in py_files:
            rel_str = str(py_path.relative_to(self.root_dir)).replace("\\", "/")
            if any(part.startswith(".") or part in ("__pycache__", "venv", ".venv") for part in py_path.parts):
                continue
            self._analyze_python_file(py_path, rel_str)

        return {
            "total_files_analyzed": len(self.imports_map),
            "total_symbols_indexed": sum(len(syms) for syms in self.symbols_map.values()),
        }

    def _analyze_python_file(self, file_path: Path, rel_path: str) -> None:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            logger.debug("Skipping unparseable syntax in %s: %s", rel_path, e)
            return

        self.imports_map[rel_path] = set()
        self.symbols_map[rel_path] = []

        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports_map[rel_path].add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                self.imports_map[rel_path].add(node.module)

            # Classes
            elif isinstance(node, ast.ClassDef):
                self.symbols_map[rel_path].append(
                    SymbolDefinition(
                        name=node.name,
                        kind="class",
                        file_path=rel_path,
                        line_number=node.lineno,
                    )
                )

            # Functions & FastAPI Routes
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                route_path, http_method = self._extract_route_info(node)
                kind = "route" if route_path else "function"
                self.symbols_map[rel_path].append(
                    SymbolDefinition(
                        name=node.name,
                        kind=kind,
                        file_path=rel_path,
                        line_number=node.lineno,
                        route_path=route_path,
                        http_method=http_method,
                    )
                )

    def _extract_route_info(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str | None, str | None]:
        for deco in node.decorator_list:
            if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
                method = deco.func.attr.upper()
                if method in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"):
                    path = "/"
                    if deco.args and isinstance(deco.args[0], ast.Constant) and isinstance(deco.args[0].value, str):
                        path = deco.args[0].value
                    return path, method
        return None, None

    def compute_blast_radius(self, target_file_or_symbol: str) -> BlastRadiusResult:
        """Calculate direct and indirect dependents, affected routes, and relevant test suites."""
        target_normalized = target_file_or_symbol.replace("\\", "/").lstrip("/")

        direct_dependents: set[str] = set()
        for file_path, imported_modules in self.imports_map.items():
            if file_path == target_normalized:
                continue
            # Check if this file imports target module
            target_module_guess = target_normalized.replace(".py", "").replace("/", ".")
            for mod in imported_modules:
                if mod in target_module_guess or target_module_guess in mod:
                    direct_dependents.add(file_path)

        # Indirect dependents
        indirect_dependents: set[str] = set()
        for file_path, imported_modules in self.imports_map.items():
            if file_path in direct_dependents or file_path == target_normalized:
                continue
            for direct in direct_dependents:
                direct_mod = direct.replace(".py", "").replace("/", ".")
                for mod in imported_modules:
                    if mod in direct_mod or direct_mod in mod:
                        indirect_dependents.add(file_path)

        all_affected = direct_dependents | indirect_dependents
        affected_tests = [f for f in all_affected if "test" in f]

        affected_routes: list[str] = []
        for file_path in [target_normalized] + list(all_affected):
            for sym in self.symbols_map.get(file_path, []):
                if sym.kind == "route" and sym.route_path:
                    affected_routes.append(f"{sym.http_method} {sym.route_path} ({file_path})")

        total = len(all_affected)
        if total == 0:
            risk = "LOW"
        elif total <= 3:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        return BlastRadiusResult(
            target=target_file_or_symbol,
            risk_tier=risk,
            direct_dependents=sorted(direct_dependents),
            indirect_dependents=sorted(indirect_dependents),
            affected_routes=sorted(affected_routes),
            affected_tests=sorted(affected_tests),
            total_affected_files=total,
        )
