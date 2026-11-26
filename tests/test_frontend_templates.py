"""The generated frontend is a complete Vite + React + Tailwind project, not just App.tsx."""

from __future__ import annotations

import json
from pathlib import Path

from nexus.providers.mock import MockProvider
from nexus.teams.it_pack import NexusITTeam
from nexus.teams.it_pack import platform_templates as tpl

EXPECTED = {
    "package.json",
    "index.html",
    "tsconfig.json",
    "vite.config.ts",
    "tailwind.config.js",
    "postcss.config.js",
    "src/main.tsx",
    "src/index.css",
}


def test_render_frontend_files_covers_a_buildable_vite_project() -> None:
    files = tpl.render_frontend_files("Watch Hub", "Watch Hub")
    assert set(files) == EXPECTED

    pkg = json.loads(files["package.json"])
    assert pkg["scripts"]["build"] == "vite build"
    assert pkg["scripts"]["typecheck"] == "tsc --noEmit"
    deps = {**pkg["dependencies"], **pkg["devDependencies"]}
    for needed in ("react", "react-dom", "vite", "@vitejs/plugin-react", "typescript", "tailwindcss", "postcss"):
        assert needed in deps
    assert deps[tpl.UI_PACKAGE] == tpl.UI_VERSION_RANGE

    tsconfig = json.loads(files["tsconfig.json"])
    assert tsconfig["compilerOptions"]["jsx"] == "react-jsx"
    assert tsconfig["include"] == ["src"]

    assert '<script type="module" src="/src/main.tsx"></script>' in files["index.html"]
    assert 'from "./App"' in files["src/main.tsx"]
    assert "./index.css" in files["src/main.tsx"]
    assert f"./node_modules/{tpl.UI_PACKAGE}/dist/**/*.js" in files["tailwind.config.js"]
    assert f"http://127.0.0.1:{tpl.CONTAINER_PORT}" in files["vite.config.ts"]


def test_main_tsx_mounts_default_or_named_export() -> None:
    main = tpl.render_frontend_main_tsx()
    assert "exported.default" in main
    assert 'typeof value === "function"' in main


def test_index_html_escapes_the_model_supplied_title() -> None:
    page = tpl.render_frontend_index_html('<script>alert("x")</script> & Co')
    assert "<script>alert" not in page
    assert "&lt;script&gt;" in page and "&amp; Co" in page
    assert "<title>Nexus App</title>" in tpl.render_frontend_index_html("   ")


def test_workspace_contains_the_full_frontend(tmp_path: Path) -> None:
    project = NexusITTeam(provider=MockProvider(), run_generated_tests=False).build_from_idea(
        "A watch tracker", output_dir=tmp_path, enable_self_healing=False
    )
    frontend = Path(project.output_path or "") / "frontend"
    present = {p.relative_to(frontend).as_posix() for p in frontend.rglob("*") if p.is_file()}
    assert EXPECTED | {"src/App.tsx", "src/api.ts"} <= present
