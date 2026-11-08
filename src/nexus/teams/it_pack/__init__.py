"""Nexus Core IT Pack: Collaborative squad of autonomous IT agents."""
from nexus.teams.it_pack.ba import BusinessAnalystAgent, ProductProposal
from nexus.teams.it_pack.designer import UiDesignerAgent, UiSpecification
from nexus.teams.it_pack.engineer import BackendEngineerAgent, BackendSpecification
from nexus.teams.it_pack.manager import EngineeringManagerAgent, SprintPlan
from nexus.teams.it_pack.qa import QaEngineerAgent, QaSpecification
from nexus.teams.it_pack.team import DeliveredProject, NexusITTeam

__all__ = [
    "NexusITTeam",
    "DeliveredProject",
    "BusinessAnalystAgent",
    "ProductProposal",
    "EngineeringManagerAgent",
    "SprintPlan",
    "UiDesignerAgent",
    "UiSpecification",
    "BackendEngineerAgent",
    "BackendSpecification",
    "QaEngineerAgent",
    "QaSpecification",
]
