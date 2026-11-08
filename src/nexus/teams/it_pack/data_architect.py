"""Nexus IT Pack: Data Architect Agent."""
from __future__ import annotations

from pydantic import BaseModel, Field
from nexus.providers.base import BaseModelProvider
from nexus.teams.it_pack.ba import ProductProposal
from nexus.teams.it_pack.solution_architect import SolutionBlueprint


class DataArchitecture(BaseModel):
    """Data domain design, relational schemas, and persistence architecture."""
    database_engine: str = Field(description="e.g. PostgreSQL 16 with asyncpg", default="PostgreSQL 16")
    tables: list[str] = Field(description="Entity table names and primary functions")
    relationships: list[str] = Field(description="Key relationships (e.g. users 1:N alerts)")
    indexes: list[str] = Field(description="Recommended performance and unique indexes")
    sql_ddl_schema: str = Field(description="Executable SQL DDL schema creating all tables, indexes, and foreign keys")


class DataArchitectAgent:
    """
    Data Architect Agent in the Nexus IT Pack.
    Designs normalized schemas, entity relationships, indexing strategies, and DDL migrations.
    """

    def __init__(self, provider: BaseModelProvider) -> None:
        self.provider = provider

    def design_data_model(self, proposal: ProductProposal, solution: SolutionBlueprint) -> DataArchitecture:
        """Formulate relational/vector data architecture and SQL schema."""
        prompt = f"""You are a Principal Data Architect.
Review the application spec:
App: {proposal.title} ({proposal.app_name})
Features: {', '.join(proposal.core_features)}
Cloud Strategy: {solution.cloud_provider} ({solution.compute_pattern})

Design the complete data architecture:
1. Identify all core database entities and relationships.
2. Define performance indexes and foreign key constraints.
3. Write clean, production-ready PostgreSQL SQL DDL statements (including UUID primary keys, created_at, updated_at).
"""
        system = "You are a meticulous Data Architect specializing in high-performance PostgreSQL database designs."
        return self.provider.structured(prompt, DataArchitecture, system_instruction=system)
