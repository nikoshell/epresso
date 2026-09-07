"""Content subsystem — data store, collections, loaders."""

from .collections import define_collection, discover_content_config, load_collections
from .store import Collection, ContentStore, Entry, RenderedContent


def reference(collection: str):
    """A content-reference field type for Pydantic schemas.

    Stores the referenced entry id as a string; resolve at render time with
    ``site.get_entry(...)`` / ``site.get_entries(...)`` (which validate and
    record the dependency edge for incremental builds).

    Example
    -------
    .. code-block:: python

        from epresso.content import reference
        class Post(BaseModel):
            author: reference("authors")
    """
    from typing import Annotated

    from pydantic import StringConstraints

    return Annotated[str, StringConstraints(min_length=1)]


__all__ = [
    "Collection",
    "ContentStore",
    "Entry",
    "RenderedContent",
    "define_collection",
    "discover_content_config",
    "load_collections",
    "reference",
]
