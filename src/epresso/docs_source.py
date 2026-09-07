"""Docs-source resolution — where a docs site reads its markdown from.

Given a project root (optionally the repo a theme declares it documents),
resolve what the docs subdir is called (``docs_dir``), which directory to read
markdown from (``base``), and whether the root is itself a git repo
(``repo_root``). No parent-walking: repo detection is current-directory only —
a root is a repo iff it has its own ``.git``. If a theme documents a repo that
*isn't* its own directory, the theme declares that explicitly (``[theme] repo``)
and passes the resolved path here as ``project_root``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_DOCS_DIR = "docs"


@dataclass(frozen=True)
class DocsSource:
    """Where a project's docs live and whether the (effective) root is a repo."""

    docs_dir: str          # subdir name used for repo-relative source prefixes
    base: Path             # directory the docs collection reads markdown from
    repo_root: Path | None  # the effective root if it is itself a git repo, else None


def resolve_docs_source(
    project_root: Path,
    *,
    docs_dir: str | None = None,
    docs_base: Path | None = None,
) -> DocsSource:
    """Resolve a project's docs source.

    ``docs_base`` overrides ``base`` (the docs-preview flow copies a repo's docs
    into a temp dir and overrides it); otherwise ``base`` is
    ``project_root/<docs_dir>``. ``repo_root`` is ``project_root`` only when that
    directory itself is a git repo (current-directory check, no parent walk).
    """
    docs_dir = (docs_dir or DEFAULT_DOCS_DIR).strip("/") or DEFAULT_DOCS_DIR
    base = docs_base.resolve() if docs_base is not None else project_root / docs_dir
    repo_root = project_root if (project_root / ".git").exists() else None
    return DocsSource(docs_dir=docs_dir, base=base, repo_root=repo_root)
