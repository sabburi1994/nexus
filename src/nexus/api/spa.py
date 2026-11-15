"""Nexus API: serve a built single page app (Vite ``dist``) safely from FastAPI.

``mount_spa(app, dist)`` adds one catch all GET/HEAD route, so register it after every API route:

* files are resolved inside ``dist`` only (``..`` segments, encoded or not, absolute paths, NUL
  bytes and symlinks pointing outside are refused);
* hashed files under ``assets/`` are cached for a year (``immutable``); ``index.html`` and the
  fixed names a PWA must revalidate (``sw.js``, ``manifest.webmanifest`` ...) get ``no-cache``;
* unknown paths fall back to ``index.html`` (client side routing), except under the API prefixes,
  which answer a JSON 404 so a typo in an API URL never returns HTML;
* content types are explicit for the files Vite emits (Windows can map ``.js`` to text/plain).
"""

from __future__ import annotations

import mimetypes
from collections.abc import Iterable
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

IMMUTABLE = "public, max-age=31536000, immutable"
NO_CACHE = "no-cache"

DEFAULT_API_PREFIXES: tuple[str, ...] = (
    "api",
    "internal",
    "health",
    "ready",
    "healthz",
    "docs",
    "redoc",
    "openapi.json",
)
DEFAULT_NO_CACHE_FILES: tuple[str, ...] = (
    "index.html",
    "sw.js",
    "registerSW.js",
    "manifest.webmanifest",
    "manifest.json",
    "theme-init.js",
)

_MEDIA_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json",
    ".map": "application/json",
    ".webmanifest": "application/manifest+json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".avif": "image/avif",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".txt": "text/plain; charset=utf-8",
    ".wasm": "application/wasm",
}


def resolve_inside(root: Path, requested: str) -> Path | None:
    """The file ``requested`` names under ``root``, or None if it is missing or escapes ``root``."""
    if not requested or "\0" in requested:
        return None
    base = root.resolve()
    try:
        candidate = (base / requested.lstrip("/")).resolve()
    except (OSError, ValueError):
        return None
    if not candidate.is_relative_to(base) or not candidate.is_file():
        return None
    return candidate


def media_type(path: Path) -> str | None:
    return _MEDIA_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0]


def mount_spa(
    app: FastAPI,
    dist: Path | str,
    *,
    api_prefixes: Iterable[str] = DEFAULT_API_PREFIXES,
    no_cache_files: Iterable[str] = DEFAULT_NO_CACHE_FILES,
    immutable_dir: str = "assets",
    other_files_cache: str = NO_CACHE,
) -> None:
    """Serve ``dist`` at ``/`` with SPA fallback; see the module docstring for the rules.

    A missing ``dist`` folder does not fail at startup (tests, API only containers): pages then
    answer 404 until a build exists.
    """
    root = Path(dist)
    prefixes = {p.strip("/") for p in api_prefixes}
    no_cache = {n.lower() for n in no_cache_files}
    immutable_prefix = immutable_dir.strip("/") + "/"

    def respond(path: Path, cache: str) -> FileResponse:
        return FileResponse(path, media_type=media_type(path), headers={"Cache-Control": cache})

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        first = full_path.split("/", 1)[0]
        if first in prefixes:
            raise HTTPException(status_code=404, detail="Not Found")
        index = resolve_inside(root, "index.html")
        found = resolve_inside(root, full_path) if full_path else None
        if found is not None and found != index:
            rel = found.relative_to(root.resolve()).as_posix()
            if rel.startswith(immutable_prefix):
                return respond(found, IMMUTABLE)
            return respond(found, NO_CACHE if found.name.lower() in no_cache else other_files_cache)
        if full_path.startswith(immutable_prefix):
            # A missing hashed asset is a stale page asking for an old build: 404, not index.html.
            raise HTTPException(status_code=404, detail="Not Found")
        if index is None:
            raise HTTPException(status_code=404, detail="Frontend build not found")
        return respond(index, NO_CACHE)
