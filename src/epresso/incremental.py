"""Incremental build graph + cache.

A path is reused from a previous build only when its ``cacheKey`` (data) and every
content-entry hash it previously rendered still match. The whole cache is dropped
when config or code/templates change (we cannot yet attribute template edits to
individual paths, so that is a coarse invalidation).

``IncrementalCache`` is the persistence adapter: it loads/saves the manifest and
copies cached output files around. ``BuildGraph`` owns the *per-render content
dependency graph* and drives the cache: Site's data API records dependency edges
through it as a route renders, and the build loop asks it whether a path can be
reused and records the new state.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .private import is_private

CACHE_VERSION = 1


def sha256_hex(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
    return h.hexdigest()


class IncrementalCache:
    """Load/save the incremental manifest and copy cached output files around."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.manifest_path = cache_dir / "incremental.json"
        self.output_dir = cache_dir / "output"
        self._prev: dict[str, Any] | None = self._load()
        self._next: dict[str, Any] = {"version": CACHE_VERSION, "configHash": "", "codeHash": "", "paths": {}}

    # -- load ----------------------------------------------------------------
    def _load(self) -> dict[str, Any] | None:
        if not self.manifest_path.exists():
            return None
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None
        return data if isinstance(data, dict) else None

    def is_usable(self, config_hash: str, code_hash: str) -> bool:
        """True if the previous manifest can be trusted for this build."""
        prev = self._prev
        return bool(
            prev
            and prev.get("version") == CACHE_VERSION
            and prev.get("configHash") == config_hash
            and prev.get("codeHash") == code_hash
        )

    # -- skip decision -------------------------------------------------------
    def can_skip(
        self, path: str, cache_key: str | None, current_digest: Callable[[str], str | None], out_rel: str
    ) -> bool:
        """Reuse the cached output for ``path`` if data + content deps are unchanged."""
        if cache_key is None:
            return False
        prev = self._prev
        if not prev:
            return False
        pe = prev.get("paths", {}).get(path)
        if not pe:
            return False
        if pe.get("cacheKey") != cache_key:
            return False
        # every content entry this path previously rendered must still match
        for key, prev_hash in (pe.get("contentHashes") or {}).items():
            if current_digest(key) != prev_hash:
                return False
        if not (self.output_dir / out_rel).exists():
            return False
        return True

    # -- file helpers --------------------------------------------------------
    def output_file(self, out_rel: str) -> Path:
        return self.output_dir / out_rel

    def store_output(self, out_rel: str, content: str) -> None:
        p = self.output_dir / out_rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    # -- manifest recording ---------------------------------------------------
    def record(self, path: str, cache_key: str | None, content_hashes: dict[str, str], out_rel: str) -> None:
        self._next["paths"][path] = {"cacheKey": cache_key, "contentHashes": content_hashes, "outputFile": out_rel}

    def carry_forward(self, path: str) -> None:
        """A skipped path keeps its previous entry so tracking survives re-renders."""
        prev = (self._prev or {}).get("paths", {}).get(path)
        if prev is not None:
            self._next["paths"][path] = prev

    def prune(self, valid_paths: set[str]) -> None:
        """Drop cached paths no longer produced this build (removed route / data)."""
        # 1) Remove output files that were cached previously but are no longer valid.
        prev_paths = ((self._prev or {}).get("paths") or {})
        for p, pe in prev_paths.items():
            if p not in valid_paths:
                out_rel = pe.get("outputFile")
                if out_rel:
                    fp = self.output_dir / out_rel
                    if fp.exists():
                        try:
                            fp.unlink()
                        except OSError:
                            pass
        # 2) Drop stale entries from the next manifest.
        for p in list(self._next.get("paths", {})):
            if p not in valid_paths:
                del self._next["paths"][p]

    def save(self, config_hash: str, code_hash: str) -> None:
        self._next["configHash"] = config_hash
        self._next["codeHash"] = code_hash
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(self._next, indent=2), encoding="utf-8")

    def clear(self) -> None:
        import shutil

        # Drop the page-output cache + manifest. Preserve the content-render cache
        # (rendered.json), which self-invalidates via its config/code hashes.
        rendered = self.cache_dir / "rendered.json"
        preserved = rendered.read_bytes() if rendered.exists() else None
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        if preserved is not None:
            rendered.parent.mkdir(parents=True, exist_ok=True)
            rendered.write_bytes(preserved)
        self._prev = None
        self._next = {"version": CACHE_VERSION, "configHash": "", "codeHash": "", "paths": {}}


class RenderedBodyCache:
    """Persisted rendered content bodies, keyed by entry digest.

    A content body (markdown → HTML) is reused across builds only while the
    markdown config and the code that feeds link resolution (templates,
    components, routes) are unchanged, so the cache is gated by the same
    config+code hashes as the incremental manifest. It survives
    :meth:`IncrementalCache.clear` because it is self-validating via those
    hashes.

    ``entries`` maps ``entry.digest`` → ``{"html": str, "metadata": dict}``.
    """

    def __init__(self, cache_dir: Path) -> None:
        self.path = cache_dir / "rendered.json"

    def load(self, config_hash: str, code_hash: str) -> dict[str, dict[str, Any]]:
        """Return valid cached entries, or ``{}`` when none are reusable."""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if data.get("configHash") != config_hash or data.get("codeHash") != code_hash:
            return {}
        entries = data.get("entries")
        return entries if isinstance(entries, dict) else {}

    def store(self, config_hash: str, code_hash: str, entries: dict[str, dict[str, Any]]) -> None:
        # Best effort: the cache is an optimisation, and a project directory can be
        # read-only (CI checkouts, sandboxes) — that must not fail a build.
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps({"configHash": config_hash, "codeHash": code_hash, "entries": entries}),
                encoding="utf-8",
            )
        except OSError:
            pass


class BuildGraph:
    """Per-render content dependency graph + the incremental cache that consumes it.

    Site's data API records dependency edges through this module as a route is
    rendered; the build loop asks it whether a path can be reused and records the
    new state. :class:`IncrementalCache` is the persistence adapter behind this
    interface.
    """

    _EXPANDING = "<expand>"

    def __init__(self, store: Any, config: Any, layer_dirs: list[Path] | None = None) -> None:
        self.store = store
        self.config = config
        self.cache = IncrementalCache(config.cache_dir())
        self._layer_dirs = list(layer_dirs or [])
        self._edges: dict[str, set[str]] = {}
        self._current: str = ""
        self._usable = False
        self._config_hash = ""
        self._code_hash = ""

    # -- dependency tracking (called by the data API during a render) --------
    def begin_route(self, path: str) -> None:
        """Start rendering ``path``; reset its dependency edge set."""
        self._current = path
        self._edges.pop(path, None)

    def end_route(self) -> None:
        self._current = ""

    def record_dependency(self, key: str) -> None:
        """Record that the current route depends on content key ``key`` (a
        ``collection:<name>`` or ``<col>:<id>`` key). No-op outside a render."""
        if self._current:
            self._edges.setdefault(self._current, set()).add(key)

    def begin_expand(self) -> None:
        """Enter route expansion (guards against recursive endpoints)."""
        self._current = self._EXPANDING

    def end_expand(self) -> None:
        self._current = ""

    @property
    def expanding(self) -> bool:
        return self._current == self._EXPANDING

    def edges_for(self, path: str) -> set[str]:
        return set(self._edges.get(path, set()))

    # -- digest resolution --------------------------------------------------
    def current_digest(self, key: str) -> str | None:
        """Current digest for a dependency key (``collection:<name>`` or ``<col>:<id>``)."""
        if key.startswith("collection:"):
            name = key[len("collection:") :]
            digests = sorted(e.digest for e in self.store.get_collection(name) if e.digest)
            return sha256_hex(*digests) if digests else ""
        col, _, eid = key.partition(":")
        entry = self.store.get_entry(col, eid)
        return entry.digest if entry else None

    def content_hashes_for(self, path: str) -> dict[str, str]:
        """Current digests of every content dependency a path rendered."""
        out: dict[str, str] = {}
        for key in self._edges.get(path, set()):
            d = self.current_digest(key)
            if d is not None:
                out[key] = d
        return out

    # -- coarse invalidation (config / code change) --------------------------
    @staticmethod
    def hash_config(config: Any) -> str:
        import json

        data = config.model_dump(exclude={"root"})
        return sha256_hex(json.dumps(data, sort_keys=True, default=str))

    @staticmethod
    def hash_code(config: Any, layer_dirs: list[Path] | None = None) -> str:
        """Hash of route/template/asset source (the 'code'), excluding data (.md in
        pages/, content collections) and generated bytecode/__pycache__."""
        files: list[tuple[str, bytes]] = []
        for base in (
            config.dir_layouts(),
            config.dir_components(),
            config.dir_pages(),
            config.dir_assets(),
            config.dir_static(),
        ):
            if not base.exists():
                continue
            for f in sorted(base.rglob("*")):
                if not f.is_file():
                    continue
                if is_private(f.relative_to(base)):
                    continue  # _-prefixed (private/draft) files are excluded from processing
                if "__pycache__" in f.parts or f.suffix.lower() in {".md", ".pyc", ".pyo"}:
                    continue
                files.append((str(f.relative_to(base)), f.read_bytes()))
        cc = config.root / "content.config.py"
        if cc.exists():
            files.append(("content.config.py", cc.read_bytes()))
        # External layers are code too: a changed local layer (or a re-fetched repo)
        # must invalidate the cache. A layer contributes only `components/` and
        # `layouts/` (ADR-0003), so hash just those. Walking the whole checkout
        # pulled in `.git/` and any stray file, reading megabytes per build and
        # invalidating the cache on every git command. Prefixed so a name shared
        # with a site root is still distinguishable.
        for i, base in enumerate(layer_dirs or []):
            for sub in ("components", "layouts"):
                root = base / sub
                if not root.is_dir():
                    continue
                for f in sorted(root.rglob("*")):
                    if not f.is_file() or "__pycache__" in f.parts:
                        continue
                    if f.suffix.lower() in {".md", ".pyc", ".pyo"}:
                        continue
                    files.append((f"layer{i}:{sub}/{f.relative_to(root)}", f.read_bytes()))
        h = hashlib.sha256()
        for rel, data in sorted(files, key=lambda x: x[0]):
            h.update(rel.encode())
            h.update(data)
        return h.hexdigest()

    # -- build coordination (drives the cache adapter) -----------------------
    def ensure_hashes(self) -> tuple[str, str]:
        """Compute the config/code hashes once and cache them on the graph."""
        if not self._config_hash:
            self._config_hash = self.hash_config(self.config)
            self._code_hash = self.hash_code(self.config, self._layer_dirs)
        return self._config_hash, self._code_hash

    def prepare(self, *, clean: bool) -> None:
        """Clear the cache when ``clean``, recompute the coarse hashes, and decide
        whether the previous manifest is usable."""
        if clean:
            self.cache.clear()
        self._config_hash, self._code_hash = self.ensure_hashes()
        self._usable = self.cache.is_usable(self._config_hash, self._code_hash)

    def can_skip(self, path: str, cache_key: str | None, out_rel: str) -> bool:
        """True if the cached output for ``path`` is reusable (usable manifest + data
        and content deps unchanged)."""
        return self._usable and self.cache.can_skip(path, cache_key, self.current_digest, out_rel)

    def reuse_output(self, path: str, out_rel: str) -> bytes:
        """Return the cached output bytes for a skipped path, carrying it forward."""
        data = self.cache.output_file(out_rel).read_bytes()
        self.cache.carry_forward(path)
        return data

    def record_rendered(self, path: str, cache_key: str | None, out_rel: str, content: str) -> None:
        """Cache a freshly rendered output along with the content hashes it depends on."""
        self.cache.store_output(out_rel, content)
        self.cache.record(path, cache_key, self.content_hashes_for(path), out_rel)

    def finish(self, valid_paths: set[str]) -> None:
        """Prune stale entries and persist the new manifest."""
        self.cache.prune(valid_paths)
        self.cache.save(self._config_hash, self._code_hash)


__all__ = ["IncrementalCache", "RenderedBodyCache", "BuildGraph", "sha256_hex"]
