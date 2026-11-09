"""Example: Programmatically invoking the Nexus 7-specialist IT Squad."""
from __future__ import annotations

from pathlib import Path
from nexus.teams.it_pack.team import NexusITTeam


def main() -> None:
    # 1. Instantiate the IT Squad
    team = NexusITTeam()

    idea = "AI-powered coffee roast recommender based on morning sleep quality"
    output_dir = Path("./sample_coffee_app")

    print(f"Starting IT Squad for: '{idea}'")

    # 2. Coordinate all 7 specialists: BA, SA, DA, UI/UX, FullStack, DevOps, QA
    project = team.build_from_idea(
        raw_user_idea=idea,
        target_cloud="gcp",
        output_dir=output_dir,
    )

    print("\n=== Project Delivered Successfully! ===")
    print(f"App Name: {project.proposal.title} ({project.proposal.app_name})")
    print(f"Stories: {len(project.proposal.user_stories)} user stories generated")
    print(f"Cloud Target: {project.solution.cloud_provider.upper()} ({project.solution.compute_pattern})")
    print(f"Tables: {', '.join(project.data_architecture.tables)}")
    print(f"UI Component: {project.ui.component_name}.tsx")
    print(f"QA Clearance: {'PASSED' if project.qa.passed_preflight else 'WARN'}")
    print(f"Saved to: {project.output_path}")


if __name__ == "__main__":
    main()
