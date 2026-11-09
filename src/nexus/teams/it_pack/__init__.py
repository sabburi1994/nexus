"""Nexus Core IT Pack: Collaborative squad of 7 autonomous IT specialists."""

from nexus.teams.it_pack.ba import BusinessAnalystAgent, ProductProposal
from nexus.teams.it_pack.data_architect import DataArchitectAgent, DataArchitecture
from nexus.teams.it_pack.designer import UiDesignerAgent, UiSpecification
from nexus.teams.it_pack.devops import DevopsEngineerAgent, DevopsSpecification
from nexus.teams.it_pack.fullstack import FullStackEngineerAgent, FullStackSpecification
from nexus.teams.it_pack.qa import QaEngineerAgent, QaSpecification
from nexus.teams.it_pack.solution_architect import (
    SolutionArchitectAgent,
    SolutionBlueprint,
)
from nexus.teams.it_pack.team import DeliveredProject, NexusITTeam

__all__ = [
    "BusinessAnalystAgent",
    "DataArchitectAgent",
    "DataArchitecture",
    "DeliveredProject",
    "DevopsEngineerAgent",
    "DevopsSpecification",
    "FullStackEngineerAgent",
    "FullStackSpecification",
    "NexusITTeam",
    "ProductProposal",
    "QaEngineerAgent",
    "QaSpecification",
    "SolutionArchitectAgent",
    "SolutionBlueprint",
    "UiDesignerAgent",
    "UiSpecification",
]
