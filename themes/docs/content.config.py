"""Docs collection — reads markdown from the project's docs directory.

``epresso_root`` is provided by the engine when this content.config is loaded
(the site/project root). Docs-source resolution lives in ``epresso.docs_source``.
A theme run at its own directory documents an enclosing repo only when it
declares it explicitly via ``[theme] repo`` (no parent-walking); the docs-preview
flow overrides ``[theme] docs_base`` instead.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel

from epresso.content import define_collection
from epresso.content.docs import DocsLoader
from epresso.docs_source import resolve_docs_source

# Site/project root, injected by the engine when content.config is loaded.
ROOT = Path(epresso_root)  # noqa: F821  (epresso_root injected by the engine)

# Docs config from this project's site.toml ([theme]).
_theme = tomllib.loads((ROOT / "site.toml").read_text(encoding="utf-8")).get("theme", {})
_docs_dir = str(_theme.get("docs_dir", "docs"))
_docs_base = _theme.get("docs_base")  # docs preview overrides the read dir
# Self-build: a theme run at its own dir documents an enclosing repo it declares.
_root_eff = ROOT
if _docs_base is None and _theme.get("repo"):
    _root_eff = (ROOT / str(_theme["repo"])).resolve()

src = resolve_docs_source(
    _root_eff,
    docs_dir=_docs_dir,
    docs_base=Path(str(_docs_base)) if _docs_base else None,
)
DOCS_GLOB = "**/*.{md,markdown}"


class Doc(BaseModel):
    """What an author writes in a doc's frontmatter."""

    title: str
    description: str = ""
    draft: bool = False   # shown in dev/preview, excluded from production builds
    private: bool = False  # _-prefixed file: shown in dev/preview, excluded from production


docs = define_collection(
    "docs",
    loader=DocsLoader(src.base, DOCS_GLOB, docs_dir=src.docs_dir),
    schema=Doc,
)
