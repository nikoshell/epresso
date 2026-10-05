"""A reusable Markdown docs-collection loader.

Reads a tree of Markdown files under a base dir and turns them into docs — one
doc per file, grouped and ordered by their directory hierarchy.

Each entry stores only its *authored*
frontmatter in ``data`` (validated against a narrow schema), while derived
values — hubs (``README.md``/``index.md``), grouping/order and circular
prev/next — live in ``entry.computed`` (see ``Entry``). Use ``DocsLoader`` as a
collection's ``loader``. On-page headings come from the render
(``Entry.headings``), so the loader does not parse every body a second time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..document import parse_document
from ..errors import ContentError
from ..markdown import first_heading, strip_first_h1
from .loaders import LoaderObject
from .store import Collection, ContentStore, Entry, content_digest


def _glob(base: Path, pattern: str) -> list[Path]:
    """Files under ``base`` matching ``pattern`` (``**/*.{a,b}`` brace-aware).

    ``_``-prefixed (private) files are included — they are tagged ``private`` and
    shown in dev/preview but excluded from production builds."""
    m = re.match(r"\*\*/\*\.\{([^}]+)\}$", pattern)
    if m:
        return sorted(p for ext in m.group(1).split(",") for p in base.rglob("*." + ext.strip()))
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
            (parts[-1] if parts else "Overview").replace("-", " ").title() if is_hub else stem.replace("-", " ").title()
        )
        body_stripped = strip_first_h1(body)
        has_page = _has_content(body_stripped)
        if doc_id in docs and is_hub and docs[doc_id]["is_hub"]:
            # README.md + index.md in one dir: one landing page — the one with a
            # body (a comment-only index.md is a placeholder), else the first.
            if not has_page or docs[doc_id]["has_page"]:
                continue
            del docs[doc_id]
        if doc_id in docs:  # collision (e.g. a hub + a same-named leaf) -> full path
            doc_id = rel.with_suffix("").as_posix()
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
            "rel": rel.as_posix(),
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
    authored ``order`` (default 1000): a directory is placed by its hub's order, or
    — when it has no hub file — by the smallest order anywhere beneath it, so a
    section can be ordered (and exist) without a landing page. A page is placed by
    its own order, hub pages lead ties. Assigns the global ``order`` and ``group``
    used by the sidebar nav and prev/next chain.
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

    def subtree_order(node: dict) -> int:
        """Smallest authored order under ``node`` — a hub's order wins where there is one."""
        best = node.get("hub_order", DEFAULT_ORDER)
        for _name, child in node.get("dirs", {}).items():
            best = min(best, subtree_order(child))
        for doc_id in node.get("docs", []):
            best = min(best, docs[doc_id]["order"])
        return best

    def walk(node: dict) -> None:
        # Interleave this directory's pages and subdirectories by authored order.
        entries: list[tuple] = []
        for name, child in node.get("dirs", {}).items():
            hub_order = child.get("hub_order")
            key = hub_order if hub_order is not None else subtree_order(child)
            entries.append((key, 0, name, ("dir", child)))
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


@dataclass(frozen=True)
class DocsMount:
    """One docs source: a Markdown dir published under a URL ``prefix``.

    ``title`` labels the source's sidebar group (non-root prefixes only);
    ``repo_url`` is the "view source" base, e.g.
    ``https://github.com/o/r/blob/v1/docs`` — each page appends its relative path.
    """

    base: Path
    prefix: str = "/"
    title: str = ""
    repo_url: str = ""
    docs_dir: str = "docs"
    asset_url: str = ""  # URL where the mount's non-Markdown files are published
    # Nested ``nav`` (``"a.md"``, ``{"Title" = "a.md"}``, ``{"Section" = [...]}``,
    # ``{"Title" = "https://..."}``). Set: it alone orders/groups the sidebar.
    nav: tuple = ()
    # Dirs (relative to ``base``) another plugin owns, e.g. epresso_blog's
    # ``blog/``: not read as docs; ``nav`` entries pointing there are dropped.
    exclude: tuple = ()


def _prefix_parts(prefix: str) -> list[str]:
    return [p for p in prefix.strip("/").split("/") if p]


def _read_mounts(mounts: list[DocsMount], pattern: str) -> dict[str, dict]:
    """Read every mount into one id space. Duplicate ids are an error; a
    non-root mount without an index gets a label-only section hub."""
    docs: dict[str, dict] = {}
    for m in mounts:
        if not m.base.exists():
            continue
        pre = _prefix_parts(m.prefix)
        for d in _read_docs(m.base, pattern, m.docs_dir).values():
            if any(d["rel"] == x or d["rel"].startswith(x.rstrip("/") + "/") for x in m.exclude):
                continue
            d["id"] = "/".join([*pre, d["id"]]) if d["id"] else "/".join(pre)
            d["group_path"] = [*pre, *d["group_path"]]
            d["source_url"] = f"{m.repo_url.rstrip('/')}/{d['rel']}" if m.repo_url else ""
            d["mount_title"] = m.title
            if m.asset_url:
                rel_dir = d["rel"].rpartition("/")[0]
                d["image_base"] = m.asset_url.rstrip("/") + "/" + (rel_dir + "/" if rel_dir else "")
            if d["id"] in docs:
                raise ContentError(
                    f"duplicate docs page {d['id'] or '/'!r}: {docs[d['id']]['file']} and {d['file']}"
                    " (give one source a different `prefix`)"
                )
            docs[d["id"]] = d
        if m.nav:
            _apply_nav(docs, m, pre)
        hub = "/".join(pre)
        if pre and hub not in docs:
            docs[hub] = {
                "id": hub,
                "file": None,
                "title": m.title or pre[-1].replace("-", " ").title(),
                "description": "",
                "draft": False,
                "private": False,
                "order": DEFAULT_ORDER,
                "source": "",
                "rel": "",
                "source_url": "",
                "mount_title": m.title,
                "group_path": pre,
                "is_hub": True,
                "has_page": False,
                "body": "",
            }
    return docs


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "section"


def _apply_nav(docs: dict[str, dict], m: DocsMount, pre: list[str]) -> None:
    """Order/group one mount's docs by its ``nav``: listed pages take the nav's
    position, title and section; sections become label-only hubs; URL entries
    become sidebar links; unlisted pages are still built but ``hidden``."""
    by_rel = {d["rel"]: d for d in docs.values() if d.get("rel") and d["file"] and d["group_path"][: len(pre)] == pre}
    mine = set(id(d) for d in by_rel.values())
    seen: set[int] = set()
    counter = [0]

    def add(item: object, path: list[str]) -> None:
        title, target = (None, item) if isinstance(item, str) else next(iter(dict(item).items()))  # type: ignore[arg-type]
        n = counter[0] = counter[0] + 1
        if isinstance(target, list):  # a section
            slug = [*path, _slug(str(title))]
            hid = "/".join(slug)
            if hid in docs:
                hid = "~nav/" + hid
            docs[hid] = {
                "id": hid,
                "file": None,
                "title": str(title),
                "description": "",
                "draft": False,
                "private": False,
                "order": n,
                "source": "",
                "rel": "",
                "source_url": "",
                "mount_title": m.title,
                "group_path": slug,
                "is_hub": True,
                "has_page": False,
                "body": "",
            }
            for child in target:
                add(child, slug)
            return
        target = str(target)
        if "://" in target or target.startswith(("/", "mailto:")):  # an external link
            lid = f"~link/{'/'.join(pre)}/{n}"
            docs[lid] = {
                "id": lid,
                "file": None,
                "title": str(title or target),
                "description": "",
                "draft": False,
                "private": False,
                "order": n,
                "source": "",
                "rel": "",
                "source_url": "",
                "link": target,
                "mount_title": m.title,
                "group_path": path,
                "is_hub": False,
                "has_page": False,
                "body": "",
            }
            return
        d = by_rel.get(target.lstrip("./"))
        if d is None and any(target.lstrip("./").startswith(x.rstrip("/") + "/") for x in m.exclude):
            return  # owned by another plugin (it adds its own sidebar entries)
        if d is None:
            raise ContentError(f"nav entry {target!r} is not a page in {m.base}")
        seen.add(id(d))
        d["order"], d["group_path"] = n, path
        if title:
            d["title"] = str(title)
        if d["id"] != "/".join(pre):  # the source's landing page stays its hub
            d["is_hub"] = False

    for item in m.nav:
        add(item, list(pre))
    for d in by_rel.values():
        if id(d) in mine and id(d) not in seen and d["id"] != "/".join(pre):
            d["hidden"], d["order"] = True, DEFAULT_ORDER * 10


class DocsLoader(LoaderObject):
    """Load markdown files into a docs collection.

    Each entry stores authored ``data`` (title/description, validated against the
    collection schema) and the derived docs-nav model in ``computed``.
    """

    def __init__(
        self,
        base: Path | None = None,
        pattern: str = "**/*.{md,markdown}",
        docs_dir: str = "docs",
        *,
        mounts: list[DocsMount] | None = None,
    ):
        """Read ``base`` (one source at ``/``), or several ``mounts``."""
        if mounts is None:
            if base is None:
                raise TypeError("DocsLoader needs a base dir or mounts")
            mounts = [DocsMount(base=base, docs_dir=docs_dir)]
        self.mounts = mounts
        self.pattern = pattern

    @property
    def base(self) -> Path:
        """The first mount's dir (single-source callers)."""
        return self.mounts[0].base

    def load(self, store: ContentStore, collection: Collection) -> None:
        docs = _read_mounts(self.mounts, self.pattern)
        if not docs:
            return
        ordered = _order(docs)
        for d in ordered:  # a titled non-root source names its own sidebar group
            if d["mount_title"] and d["group_path"]:
                d["group"] = d["mount_title"]
        chain = [d for d in ordered if d["id"] != "" and d.get("has_page", True) and not d.get("hidden")]
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
            if doc["id"] in index and n > 1:
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
                "source_url": doc["source_url"],
                "image_base": doc.get("image_base", ""),
                "hidden": doc.get("hidden", False),
                "link": doc.get("link", ""),
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
