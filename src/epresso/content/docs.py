"""A reusable Markdown docs-collection loader.

Reads a tree of Markdown files under a base dir and turns them into docs — one
doc per file, grouped and ordered by their directory hierarchy.

Each entry stores only its *authored*
frontmatter in ``data`` (validated against a narrow schema), while derived
values — hubs (``README.md``/``index.md``), grouping/order, on-page headings and
circular prev/next — live in ``entry.computed`` (see ``Entry``). Use
``DocsLoader`` as a collection's ``loader``.
"""

from __future__ import annotations

import re
from pathlib import Path

from markdown_it import MarkdownIt

from ..document import parse_document
from ..markdown import first_heading, headings, strip_first_h1
from .loaders import LoaderObject
from .store import Collection, ContentStore, Entry, content_digest

_MD = MarkdownIt("commonmark", {"html": True}).enable("table")


def _glob(base: Path, pattern: str) -> list[Path]:
    """Files under ``base`` matching ``pattern`` (``**/*.{a,b}`` brace-aware).

    ``_``-prefixed (private) files are included — they are tagged ``private`` and
    shown in dev/preview but excluded from production builds."""
    m = re.match(r"\*\*/\*\.\{([^}]+)\}$", pattern)
    if m:
        return sorted(
            p for ext in m.group(1).split(",") for p in base.rglob("*." + ext.strip())
        )
    return sorted(base.glob(pattern))


def _has_content(body: str) -> bool:
    """True if ``body`` isn't effectively empty (comment/whitespace only)."""
    t = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    t = re.sub(r"\[//\]:\s*<[^>]*>\s*(?:\([^)]*\))?", "", t)
    return bool(t.strip())


# Default order when a doc (or a category without an index hub) sets none.
# Large so unordered items sort after curated ones, before alphabetical ties.
DEFAULT_ORDER = 1000


def _int_order(value: object, default: int = DEFAULT_ORDER) -> int:
    """Parse an authored ``order`` frontmatter value to an int (default when absent)."""
    if value is None:
        return default
    if not isinstance(value, (int, float, str, bytes, bytearray)):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _read_docs(base: Path, pattern: str, docs_dir: str) -> dict[str, dict]:
    """Read every file into a raw doc: file-derived id/group/source plus authored
    ``title``/``description``/``draft`` and the parsed ``body``. A lone
    ``<dir>/index.md`` collapses to a flat root-level page (like ``<dir>.md``).
    A ``_``-prefixed file/dir is tagged ``private``."""
    from ..private import is_private as _is_private  # noqa: PLC0415

    docs: dict[str, dict] = {}
    for path in _glob(base, pattern):
        doc = parse_document(path.read_text(encoding="utf-8"), "markdown")
        fm, body = doc.data or {}, doc.body
        rel = path.relative_to(base)
        parts = list(rel.parts[:-1])
        stem = rel.stem
        is_hub = stem.lower() in {"readme", "index"}
        doc_id = "/".join(parts) if is_hub else rel.with_suffix("").as_posix()
        name = (
            (parts[-1] if parts else "Overview").replace("-", " ").title()
            if is_hub
            else stem.replace("-", " ").title()
        )
        if doc_id in docs:  # collision (e.g. a hub + a same-named leaf) -> full path
            doc_id = rel.with_suffix("").as_posix()
        body_stripped = strip_first_h1(body)
        has_page = _has_content(body_stripped)
        # A hub with no body is a category label only (no page generated); any
        # other empty file is ignored entirely.
        if not has_page and not is_hub:
            continue
        docs[doc_id] = {
            "id": doc_id,
            "file": path,
            "title": str(fm.get("title") or first_heading(body) or name),
            "description": str(fm.get("description", "")),
            "draft": bool(fm.get("draft", False)),
            "private": bool(_is_private(rel)),
            "order": _int_order(fm.get("order")),
            # Repo-root-relative source for "view/edit this page" links: prefix the
            # file's path under the docs dir with the docs-dir name, so it always
            # reads ``docs/basics/components.md`` — regardless of whether the docs
            # are read from the project root or a copied base (preview).
            "source": f"{docs_dir}/{rel.as_posix()}" if docs_dir else str(rel),
            "group_path": parts,
            "is_hub": is_hub,
            "has_page": has_page,
            "body": body_stripped,
        }
    _flatten_lone_hubs(docs)
    return docs


def _flatten_lone_hubs(docs: dict[str, dict]) -> None:
    """A hub that is the only file in its dir (``<dir>/index.md`` alone) is a flat
    ``<dir>.md`` page — drop it to root level so it renders/orders like one."""
    dirs: dict[tuple, int] = {}
    for d in docs.values():
        gp = tuple(d["group_path"])
        dirs[gp[:1]] = dirs.get(gp[:1], 0) + 1
    for d in docs.values():
        if d["is_hub"] and len(d["group_path"]) == 1 and dirs[tuple(d["group_path"][:1])] == 1:
            d["group_path"] = []


def _order(docs: dict[str, dict]) -> list[dict]:
    """Order docs by directory hierarchy, respecting curated frontmatter order.

    Within a directory, pages and subdirectories are interleaved by their
    authored ``order`` (default 1000): a directory is placed by its hub's order,
    a page by its own, hub pages lead ties. Assigns the global ``order`` and
    ``group`` used by the sidebar nav and prev/next chain.
    """
    root: dict = {}
    for doc_id, d in docs.items():
        node = root
        for part in d["group_path"]:
            node = node.setdefault("dirs", {}).setdefault(part, {})
        node.setdefault("docs", []).append(doc_id)
        if d["is_hub"]:
            node["hub_order"] = min(node.get("hub_order", DEFAULT_ORDER), d["order"])

    ordered: list[str] = []

    def walk(node: dict) -> None:
        # Interleave this directory's pages and subdirectories by authored order.
        entries: list[tuple] = []
        for name, child in node.get("dirs", {}).items():
            entries.append((child.get("hub_order", DEFAULT_ORDER), 0, name, ("dir", child)))
        for i in node.get("docs", []):
            d = docs[i]
            entries.append((d["order"], 0 if d["is_hub"] else 1, d["title"].lower(), ("doc", i)))
        for _o, _k, _tie, payload in sorted(entries, key=lambda e: e[:3]):
            if payload[0] == "dir":
                walk(payload[1])
            else:
                ordered.append(payload[1])

    walk(root)
    if "" in ordered:  # the root overview (homepage) leads the chain.
        ordered.remove("")
        ordered.insert(0, "")
    for i, doc_id in enumerate(ordered):
        d = docs[doc_id]
        d["order"] = i
        d["group"] = d["group_path"][0].replace("-", " ").title() if d["group_path"] else ""
    return [docs[i] for i in ordered]


class DocsLoader(LoaderObject):
    """Load markdown files into a docs collection.

    Each entry stores authored ``data`` (title/description, validated against the
    collection schema) and the derived docs-nav model in ``computed``.
    """

    def __init__(self, base: Path, pattern: str, docs_dir: str = "docs"):
        self.base = base
        self.pattern = pattern
        self.docs_dir = docs_dir

    def load(self, store: ContentStore, collection: Collection) -> None:
        if not self.base.exists():
            return
        docs = _read_docs(self.base, self.pattern, self.docs_dir)
        ordered = _order(docs)
        chain = [d for d in ordered if d["id"] != "" and d.get("has_page", True)]
        n = len(chain)
        index = {d["id"]: i for i, d in enumerate(chain)}
        for doc in ordered:
            authored = {
                "title": doc["title"],
                "description": doc["description"],
                "draft": doc.get("draft", False),
                "private": doc.get("private", False),
            }
            data = collection.schema.model_validate(authored) if collection.schema else authored
            prev = nxt = None
            if doc["id"] != "" and doc.get("has_page", True) and n > 1:
                i = index[doc["id"]]
                prev = chain[i - 1]
                nxt = chain[(i + 1) % n]
            computed = {
                "group": doc["group"],
                "group_path": doc["group_path"],
                "is_hub": doc["is_hub"],
                "has_page": doc.get("has_page", True),
                "order": doc["order"],
                "source": doc["source"],
                "headings": headings(_MD, doc["body"]),
                "prev": {"url": f"/{prev['id']}/", "title": prev["title"]} if prev else None,
                "next": {"url": f"/{nxt['id']}/", "title": nxt["title"]} if nxt else None,
            }
            entry = Entry(
                id=doc["id"],
                data=data,
                file_path=doc["file"],
                body=doc["body"],
                digest=content_digest(doc["body"], data),
                computed=computed,
            )
            collection._entries[doc["id"]] = entry
