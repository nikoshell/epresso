"""Helpers for skipping private (underscore-prefixed) files and directories."""

from __future__ import annotations

from pathlib import Path


def is_private(path: Path) -> bool:
    """Return ``True`` if any path segment (file or directory) starts with ``_``.

    Files/dirs prefixed with ``_`` (e.g. ``_draft.md``, ``_partials/``) are treated
    as private and excluded from builds (the Jekyll convention).
    """
    return any(part.startswith("_") for part in path.parts)
