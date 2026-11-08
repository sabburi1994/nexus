"""Nexus CLI: Developer tools for scaffolding apps and testing Google Cloud Vertex AI."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from nexus import __version__
from nexus.ai.client import GeminiClient, get_gcp_access_token, get_gcp_project


def check_ai_cmd(model: str = "gemini-3.8-flash", project: str | None = None) -> int:
    """Verify connectivity to Google Cloud Vertex AI and Gemini 3.8 Flash."""
    project_id = project or get_gcp_project()
    token = get_gcp_access_token()

    print(f"--- Checking Nexus AI Connection ---\nProject: {project_id}\nModel: {model}")

    if not token and not os.getenv("GEMINI_API_KEY"):
        print("FAIL: No GCP OAuth access token or GEMINI_API_KEY available.")
        print("Hint: Run 'gcloud auth application-default login' or configure IAM service account.")
        return 1

    if token:
        print(f"Acquired GCP Bearer Token: {token[:12]}... (cached)")

    try:
        client = GeminiClient(project_id=project_id, default_model=model)
        start_msg = "Hello from Nexus Framework. Confirm you are Gemini 3.8 Flash in one sentence."
        resp = client.generate(start_msg)
        print("SUCCESS: Vertex AI responded!")
        print(f"\"{resp.text}\"")
        print(f"Usage: {resp.input_tokens} input tokens, {resp.output_tokens} output tokens. Cost: ${resp.cost_usd:.6f} USD")
        return 0
    except Exception as exc:
        print(f"FAIL: Call to Vertex AI failed: {exc}")
        return 1


def scaffold_new_app(app_name: str, output_dir: Path) -> Path:
    """Scaffold a new microservice/app powered by the Nexus Framework."""
    target = output_dir / app_name
    if target.exists():
        raise FileExistsError(f"Target path {target} already exists.")

    print(f"Scaffolding new Nexus application: {app_name}...")

    # Create directories
    (target / "src" / app_name).mkdir(parents=True, exist_ok=True)
    (target / "tests").mkdir(parents=True, exist_ok=True)

    # Write pyproject.toml
    pyproject_content = f"""[project]
name = "{app_name}"
version = "0.1.0"
description = "{app_name} microservice powered by Nexus Framework"
requires-python = ">=3.11"
dependencies = [
    "nexus-framework>=0.1.0",
    "uvicorn>=0.30.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
    (target / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    # Write main app file
    main_py_content = f"""\"\"\"{app_name} main service application entry point.\"\"\"
from nexus.api import create_nexus_app
from nexus.ai import GeminiClient

app = create_nexus_app(
    title="{app_name}",
    description="{app_name} service powered by Nexus Framework & Gemini 3.8",
)

ai_client = GeminiClient()

@app.get("/api/ai/ask")
async def ask_ai(prompt: str) -> dict[str, str]:
    resp = ai_client.generate(prompt)
    return {{"response": resp.text, "model": resp.model}}
"""
    (target / "src" / app_name / "main.py").write_text(main_py_content, encoding="utf-8")
    (target / "src" / app_name / "__init__.py").write_text("", encoding="utf-8")

    # Write Dockerfile
    dockerfile_content = """FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir uvicorn fastapi httpx pydantic nexus-framework
COPY . .
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
"""
    (target / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")

    print(f"Application created successfully at {target}!")
    return target


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="nexus",
        description="Nexus Platform Framework: Scaffolding, AI verification, and cloud tools.",
    )
    parser.add_argument("--version", action="version", version=f"Nexus Framework v{__version__}")
    subparsers = parser.add_subparsers(dest="command")

    # check-ai
    ai_parser = subparsers.add_parser("check-ai", help="Verify Vertex AI & Gemini 3.8 Flash connectivity.")
    ai_parser.add_argument("--model", default="gemini-3.8-flash", help="Model ID")
    ai_parser.add_argument("--project", default=None, help="GCP Project ID")

    # new
    new_parser = subparsers.add_parser("new", help="Scaffold a new Nexus application.")
    new_parser.add_argument("name", help="Name of application to scaffold")
    new_parser.add_argument("--output-dir", default=".", help="Directory where app will be created")

    args = parser.parse_args()
    if args.command == "check-ai":
        sys.exit(check_ai_cmd(model=args.model, project=args.project))
    elif args.command == "new":
        scaffold_new_app(args.name, Path(args.output_dir))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
