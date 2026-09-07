"""Collection loaders — glob (filesystem) and python-defined (incl. remote data)."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Iterable
from pathlib import Path
from typing import Any

from ..document import parse_document
from ..errors import ContentError
from .store import Collection, ContentStore, Entry, content_digest

# A loader yields raw entries: {id, body?, data?}
LoaderResult = Iterable[dict[str, Any]] | Awaitable[Iterable[dict[str, Any]]]
Loader = Callable[..., LoaderResult]


def _glob_files(base: Path, pattern: str) -> list[Path]:
    """Glob ``base`` for ``pattern``, expanding ``{a,b}`` brace alternation.

    ``_``-prefixed files/dirs (private) are excluded.
    """
    from ..private import is_private

    out: set[Path] = set()
    for pat in _expand_braces(pattern):
        if "**" in pat:
            out.update(base.glob(pat))
        else:
            out.update(base.glob(pat))
    return sorted(f for f in out if not is_private(f.relative_to(base)))


def _expand_braces(pattern: str) -> list[str]:
    """Expand ``{a,b,c}`` into a list of concrete patterns."""
    import re

    m = re.search(r"\{([^}]*)\}", pattern)
    if not m:
        return [pattern]
    prefix, suffix = pattern[: m.start()], pattern[m.end():]
    out: list[str] = []
    for alt in m.group(1).split(","):
        out.extend(_expand_braces(prefix + alt + suffix))
    return out


class LoaderObject:
    """Marker base for object loaders (a ``.load(store, collection)`` method).

    ``define_collection`` uses instances of this as-is instead of wrapping a
    plain function in ``PythonLoader``, so a loader can attach derived values
    (e.g. ``entry.computed``) that live outside the schema-validated ``data``.
    """

    def load(self, store: ContentStore, collection: Collection) -> None:  # pragma: no cover
        raise NotImplementedError


class GlobLoader(LoaderObject):
    """Load markdown/json/yaml files matching a pattern under a base dir."""

    def __init__(self, pattern: str, *, base: Path, generate_id: Callable[[str], str] | None = None):
        self.pattern = pattern
        self.base = base
        self.generate_id = generate_id

    def _id_for(self, rel_path: Path) -> str:
        if self.generate_id:
            return self.generate_id(rel_path.as_posix())
        # default: path relative to base, without extension
        return str(rel_path.with_suffix(""))

    def load(self, store: ContentStore, collection: Collection) -> None:
        if not self.base.exists():
            return
        files = _glob_files(self.base, self.pattern)
        for f in files:
            if not f.is_file():
                continue
            raw = f.read_text(encoding="utf-8")
            if f.suffix.lower() in {".md", ".mdx", ".markdown"}:
                doc = parse_document(raw, "markdown")
                entry_data, entry_body = doc.data or {}, doc.body
            else:
                # JSON/YAML data collection: whole file is data, body empty.
                entry_data = _parse_data_file(f)
                entry_body = ""
            entry_id = self._id_for(f.relative_to(self.base))
            if collection.schema is not None:
                entry_data = collection.schema.model_validate(entry_data)
            entry = Entry(
                id=entry_id,
                data=entry_data,
                file_path=f,
                body=entry_body,
                digest=content_digest(entry_body, entry_data),
            )
            collection._entries[entry_id] = entry


def _parse_data_file(path: Path) -> dict[str, Any]:
    import json

    import yaml

    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() in {".json"}:
            return json.loads(text)
        return yaml.safe_load(text) or {}
    except Exception as e:  # noqa: BLE001
        raise ContentError(f"invalid data file {path.name}: {e}", path=str(path)) from e


class PythonLoader(LoaderObject):
    """Wrap a user-provided loader function (sync or async) into a Collection loader.

    The function returns an iterable (or awaitable iterable) of
    ``{"id": str, "data": dict, "body": str?}``. Useful for remote/derived data.
    """

    def __init__(self, fn: Loader):
        self.fn = fn

    def load(self, store: ContentStore, collection: Collection) -> None:
        result = self.fn()
        if inspect.isawaitable(result):
            import asyncio

            result = asyncio.run(result)  # type: ignore[arg-type]
        items = list(result)
        for item in items:
            data = dict(item.get("data") or {})
            body = item.get("body", "")
            if collection.schema is not None:
                data = collection.schema.model_validate(data)
            entry = Entry(
                id=str(item["id"]),
                data=data,
                body=body,
                digest=content_digest(body, data),
            )
            collection._entries[str(item["id"])] = entry
