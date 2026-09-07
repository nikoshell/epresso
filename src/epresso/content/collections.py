"""Collection registry — ``define_collection`` and discovery of ``content.config.py``."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .loaders import GlobLoader, LoaderObject, PythonLoader
from .store import Collection, ContentStore


class define_collection:
    """Declare a content collection.

    Examples
    --------
    .. code-block:: python

        posts = define_collection(
            "posts",
            glob="**/*.md",
            base="./content/posts",
            schema=PostSchema,
        )
    """

    def __init__(
        self,
        name: str,
        *,
        glob: str | None = None,
        base: str = "./content",
        generate_id: Callable[[str], str] | None = None,
        schema: type | None = None,
        loader: Any | None = None,
    ) -> None:
        self.name = name
        if loader is not None and isinstance(loader, LoaderObject):
            self.loader_obj: Any = loader
        elif loader is not None:
            self.loader_obj: Any = PythonLoader(loader)
        elif glob is not None:
            self.loader_obj = GlobLoader(glob, base=Path(base), generate_id=generate_id)
        else:
            raise ValueError(f"collection {name!r} needs a glob pattern or a loader function")
        self.schema = schema

    def install(self, store: ContentStore) -> Collection:
        col = Collection(self.name, schema=self.schema, loader=self.loader_obj, base=Path("."))
        store.register(col)
        return col


def discover_content_config(root: Path) -> list[Any]:
    """Import ``content.config.py`` at ``root`` and return its collections.

    The module defines collections by calling ``define_collection`` and assigning
    them to module attributes; we scan for ``define_collection`` instances.
    """
    path = root / "content.config.py"
    if not path.exists():
        return []
    spec = importlib.util.spec_from_file_location("_epresso_content_config", path)
    if spec is None or spec.loader is None:
        return []
    module = importlib.util.module_from_spec(spec)
    # make the module importable so relative imports inside it work
    sys.modules["_epresso_content_config"] = module
    # expose the site/project root so content.config can resolve paths relative
    # to the real site root (docs theme uses it for docs-source resolution).
    # Injected via __dict__ (not an attribute set) so pyright accepts it.
    module.__dict__["epresso_root"] = root
    spec.loader.exec_module(module)
    collections: list[Any] = []
    for value in vars(module).values():
        if isinstance(value, define_collection):
            collections.append(value)
    return collections


def load_collections(store: ContentStore, root: Path) -> None:
    """Discover content.config.py, install collections, resolve bases, run loaders."""
    for dc in discover_content_config(root):
        col = dc.install(store)
        # Resolve the loader's base directory relative to the site root (not cwd).
        if isinstance(col.loader, GlobLoader):
            col.loader.base = (root / col.loader.base).resolve()
        col.loader.load(store, col)
