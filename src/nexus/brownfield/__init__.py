"""Nexus Brownfield package: Legacy codebase auditing, AST dependency mapping, and blast-radius-aware refactoring."""

from nexus.brownfield.analyzer import (
    AstDependencyMapper,
    BlastRadiusResult,
    SymbolDefinition,
)
from nexus.brownfield.auditor import (
    CodebaseAuditReport,
    CodebaseAuditor,
    SecurityFinding,
)
from nexus.brownfield.refactor import (
    BrownfieldRefactorer,
    FilePatch,
    RefactorPlan,
)

__all__ = [
    "AstDependencyMapper",
    "BlastRadiusResult",
    "SymbolDefinition",
    "CodebaseAuditReport",
    "CodebaseAuditor",
    "SecurityFinding",
    "BrownfieldRefactorer",
    "FilePatch",
    "RefactorPlan",
]
