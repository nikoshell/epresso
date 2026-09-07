"""epresso content model — a collection-keyed immutable data store.

A collection-keyed store: ``Map<collection, Map<id, entry>>`` where an
entry is ``{id, data, filePath, body, digest, rendered}``. ``digest`` drives
incremental rebuilds.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RenderedContent:
    html: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Entry[T]:
    """A single content entry in a collection.

    ``data`` is the schema-validated *authored* content (frontmatter). Values
    computed by the loader/derive step (ordering, grouping, nav) live in
    ``computed`` — so a schema validates what an author
    writes and derived data is produced separately.
    """

    id: str
    data: T
    file_path: Path | None = None
    body: str = ""
    digest: str = ""
    rendered: RenderedContent | None = None
    computed: dict[str, Any] | None = None  # derived (non-authored) values

    @property
    def slug(self) -> str:
        """Entry id without file extension (e.g. ``my-post.md`` → ``my-post``)."""
        return self.id

    @property
    def headings(self) -> list[dict[str, Any]]:
        if not self.rendered:
            return []
        return self.rendered.metadata.get("headings", [])


def content_digest(body: str, data: Any) -> str:
    """Stable digest over body + data — the incremental invalidation key."""
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    h = hashlib.sha256()
    h.update(body.encode("utf-8"))
    h.update(repr(sorted(data.items(), key=lambda kv: str(kv[0]))).encode("utf-8"))
    return h.hexdigest()


class Collection:
    """A named group of entries, validated against an optional Pydantic schema."""

    def __init__(
        self,
        name: str,
        *,
        schema: type | None = None,
        loader: Any = None,
        base: Path | None = None,
    ) -> None:
        self.name = name
        self.schema = schema
        self.loader = loader
        self.base = base
        self._entries: dict[str, Entry] = {}

    @property
    def entries(self) -> dict[str, Entry]:
        return self._entries

    def get(self, entry_id: str) -> Entry | None:
        return self._entries.get(entry_id)

    def all(self, *, sorted: bool = True) -> list[Entry]:
        items = list(self._entries.values())
        if sorted:
            # Deterministic ordering: stable by id.
            items.sort(key=lambda e: e.id)
        return items

    def __len__(self) -> int:
        return len(self._entries)


class ContentStore:
    """Immutable collection-keyed data store."""

    def __init__(self) -> None:
        self._collections: dict[str, Collection] = {}

    def register(self, collection: Collection) -> None:
        if collection.name in self._collections:
            raise ValueError(f"collection already registered: {collection.name}")
        self._collections[collection.name] = collection

    def collection(self, name: str) -> Collection:
        try:
            return self._collections[name]
        except KeyError:
            raise KeyError(f"unknown collection: {name!r}") from None

    def get_entry(self, collection: str, entry_id: str) -> Entry | None:
        col = self._collections.get(collection)
        return col.get(entry_id) if col else None

    def get_collection(self, name: str) -> list[Entry]:
        return self._collections[name].all() if name in self._collections else []

    @property
    def collections(self) -> dict[str, Collection]:
        return self._collections

    def names(self) -> list[str]:
        return sorted(self._collections)
