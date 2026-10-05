"""Bundled epresso plugin: a blog — MkDocs / Material blog posts, unchanged.

Enable it from ``site.toml`` (the docs theme does)::

    plugins = ["epresso_blog"]

    [plugin.epresso_blog]                   # MkDocs blog plugin options and defaults
    blog_dir = "blog"                       # posts in <blog_dir>/posts/ (under the docs dir,
                                            # or content/ on a site without epresso_docs)
    post_url_format = "{date}/{slug}"       # {date} = YYYY/MM/DD, also {slug}, {file}, {categories}
    post_slugify = "title"                  # "title" or "file"
    pagination_per_page = 10
    archive = true                          # <blog>/archive/<year>/
    categories = true                       # <blog>/category/<name>/
    authors_file = "{blog_dir}/.authors.yml"
    draft = false                           # publish drafts in production
    rss = true                              # <blog>/rss.xml
    layout = "DocsPage"                     # page layout (default: DocsPage with epresso_docs, else Base)

A post is Markdown with MkDocs' frontmatter (``date`` — a date, datetime or
``{created: …}`` — ``authors``, ``categories``, ``tags``, ``draft``, ``slug``);
``<!-- more -->`` ends its excerpt. ``<blog_dir>/index.md`` opens the index page.
The pages render with the ``BlogIndex`` / ``BlogPost`` / ``BlogArchive``
components, which a site overrides by shipping its own.
"""

from __future__ import annotations

import datetime as dt
import re
import unicodedata
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from epresso.content.loaders import LoaderObject
from epresso.content.store import Entry, content_digest
from epresso.document import parse_document
from epresso.markdown import first_heading, strip_first_h1
from epresso.plugins import Plugin

FILES = Path(__file__).resolve().parent / "epresso_blog_files"
DEFAULTS: dict[str, Any] = {
    "blog_dir": "blog",
    "post_url_format": "{date}/{slug}",
    "post_slugify": "title",
    "pagination_per_page": 10,
    "archive": True,
    "categories": True,
    "authors_file": "{blog_dir}/.authors.yml",
    "draft": False,
    "rss": True,
}
SIDEBAR_POSTS = 10


class Post(BaseModel):
    title: str
    description: str = ""
    date: str = ""
    authors: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    draft: bool = False


def slugify(text: str) -> str:
    """ASCII-fold, drop punctuation, hyphenate (the slug format imported blogs use)."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def _date(value: Any) -> dt.datetime | None:
    if isinstance(value, dict):  # date: {created: …, updated: …}
        value = value.get("created")
    if isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.date):
        return dt.datetime(value.year, value.month, value.day)
    if isinstance(value, str) and value.strip():
        try:
            return dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _under(*parts: str) -> str:
    segs = [p for part in parts for p in str(part).split("/") if p]
    return "/" + "/".join(segs) + "/" if segs else "/"


class BlogLoader(LoaderObject):
    """Posts → entries with ``computed`` URL, date, authors and categories."""

    def __init__(self, base: Path, opts: dict[str, Any], url_root: str, authors: dict[str, dict]) -> None:
        self.base, self.opts, self.url_root, self.authors = base, opts, url_root, authors

    def load(self, store: Any, collection: Any) -> None:
        posts = self.base / "posts"
        files = sorted(posts.rglob("*.md")) if posts.is_dir() else []
        if (self.base / "index.md").is_file():
            files.append(self.base / "index.md")
        seen: dict[str, Path] = {}
        for path in files:
            doc = parse_document(path.read_text(encoding="utf-8"), "markdown")
            fm, body = doc.data or {}, doc.body
            is_index = path == self.base / "index.md"
            title = str(fm.get("title") or first_heading(body) or path.stem.replace("-", " ").title())
            title = re.sub(r"`([^`]*)`", r"\1", title)  # plain-text title (slug, <title>, cards)
            when = _date(fm.get("date"))
            if not is_index and when is None:
                from epresso.errors import ContentError  # noqa: PLC0415

                raise ContentError(f"blog post without a date: {path}")
            cats = [str(c) for c in fm.get("categories") or []]
            if is_index or when is None:
                eid, url = "__index__", self.url_root
            else:
                slug = str(fm.get("slug") or (slugify(title) if self.opts["post_slugify"] == "title" else path.stem))
                rel = self.opts["post_url_format"].format(
                    date=when.strftime("%Y/%m/%d"),
                    slug=slug,
                    file=path.stem,
                    categories="/".join(slugify(c) for c in cats),
                )
                url = _under(self.url_root, rel)
                eid = url.strip("/")
                if eid in seen:
                    from epresso.errors import ContentError  # noqa: PLC0415

                    raise ContentError(f"two blog posts have the URL {url}: {seen[eid]} and {path}")
                seen[eid] = path
            data = collection.schema.model_validate(
                {
                    "title": title,
                    "description": str(fm.get("description") or "").strip(),
                    "date": when.date().isoformat() if when else "",
                    "authors": [str(a) for a in fm.get("authors") or []],
                    "categories": cats,
                    "tags": [str(t) for t in fm.get("tags") or []],
                    "draft": bool(fm.get("draft", False)),
                }
            )
            body = strip_first_h1(body)
            rel_dir = path.parent.relative_to(self.base).as_posix()
            collection._entries[eid] = Entry(
                id=eid,
                data=data,
                file_path=path,
                body=body,
                digest=content_digest(body, data),
                computed={
                    "kind": "index" if is_index else "post",
                    "url": url,
                    "year": when.year if when else 0,
                    "date_display": f"{when:%B} {when.day}, {when.year}" if when else "",
                    "authors": [self.authors.get(a, {"name": a}) for a in data.authors],
                    "category_links": [{"name": c, "url": _under(self.url_root, "category", slugify(c))} for c in cats],
                    # relative images: <blog_dir>/posts/ is published at <url>/posts/
                    "image_base": _under(self.url_root, "" if rel_dir == "." else rel_dir),
                },
            )


def _read_authors(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    import yaml  # noqa: PLC0415

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    authors = data.get("authors", data) if isinstance(data, dict) else {}
    return {str(k): {"key": str(k), **(v or {})} for k, v in authors.items()}


def _sidebar(site: Any, opts: dict[str, Any]) -> None:
    """Docs theme: a "Blog" sidebar section — the index and the newest posts."""
    docs = site.store.collections.get("docs")
    blog = site.store.collections.get("blog")
    if docs is None or blog is None:
        return
    root = opts["_url"]
    hub_path = [p for p in root.split("/") if p]
    posts = sorted(
        (e for e in blog.all() if e.computed["kind"] == "post" and not e.data.draft),
        key=lambda e: e.data.date,
        reverse=True,
    )
    existing = next(
        (
            e
            for e in docs.all()
            if (e.computed or {}).get("is_hub") and (e.computed or {}).get("group_path") == hub_path
        ),
        None,
    )
    if existing is not None:
        order = int(existing.computed.get("order", 0))
    else:
        order = max((int((e.computed or {}).get("order", 0)) for e in docs.all()), default=0) + 1
        docs._entries["~blog"] = _link(docs, "~blog", "Blog", "", hub_path, order, hub=True)
    docs._entries["~blog/all"] = _link(docs, "~blog/all", "All posts", root, hub_path, order)
    for i, e in enumerate(posts[:SIDEBAR_POSTS], 1):
        eid = f"~blog/{e.id}"
        docs._entries[eid] = _link(docs, eid, e.data.title, e.computed["url"], hub_path, order + i)


def _link(docs: Any, eid: str, title: str, url: str, group_path: list[str], order: int, *, hub: bool = False) -> Entry:
    data = docs.schema.model_validate({"title": title}) if docs.schema else {"title": title}
    return Entry(
        id=eid,
        data=data,
        digest=content_digest(url, data),
        computed={
            "group": "",
            "group_path": group_path,
            "is_hub": hub,
            "has_page": False,
            "order": order,
            "source": "",
            "source_url": "",
            "image_base": "",
            "hidden": False,
            "link": url,
            "prev": None,
            "next": None,
        },
    )


def before_load(caps) -> None:
    config = caps.config
    opts = {**DEFAULTS, **caps.options}
    blog_dir = str(opts["blog_dir"]).strip("/") or "blog"
    docs = caps.site.store.collections.get("docs")
    mounts = getattr(getattr(docs, "loader", None), "mounts", None)
    if mounts:  # under the (first) docs source
        root, prefix = mounts[0].base, mounts[0].prefix
    else:
        root, prefix = config.dir_content(), "/"
    base = (root / blog_dir).resolve()
    if not (base / "posts").is_dir():
        return  # no blog here: no collection, routes or sidebar entry
    url_root = _under(prefix, blog_dir)
    authors = _read_authors(root / str(opts["authors_file"]).format(blog_dir=blog_dir))
    layout = opts.get("layout") or ("DocsPage" if "epresso_docs" in config.plugins else "Base")
    # What the page template reads (strings/numbers only: it's part of the config hash).
    config.plugin.setdefault("epresso_blog", {})["_resolved"] = {
        **{k: v for k, v in opts.items() if k != "_resolved"},
        "_url": url_root,
        "layout": layout,
    }
    if opts["draft"]:
        config.content.show_drafts = True
    caps.register_collection("blog", loader=BlogLoader(base, opts, url_root, authors), schema=Post)
    caps.add_layer(FILES)
    # The layout is a component name, and .ep tags are static: write the page
    # with the configured layout in place of the <BlogLayout> placeholder.
    page = config.cache_dir() / "blog" / "blog.ep"
    page.parent.mkdir(parents=True, exist_ok=True)
    src = (FILES / "pages" / "blog.ep").read_text(encoding="utf-8").replace("BlogLayout", str(layout))
    if not page.is_file() or page.read_text(encoding="utf-8") != src:
        page.write_text(src, encoding="utf-8")
    caps.add_route(f"{blog_dir}/[...path].ep", page)
    if opts["rss"]:
        caps.add_route(f"{blog_dir}/rss.xml.ep", FILES / "pages" / "rss.xml.ep")
    if (base / "posts").is_dir():  # post images, relative to the post file
        caps.add_static(base / "posts", _under(url_root, "posts"))
    _sidebar(caps.site, config.plugin["epresso_blog"]["_resolved"])


def epresso_blog() -> Plugin:
    # priority 10: after epresso_docs, whose first source holds <blog_dir>/
    return Plugin(name="epresso_blog", priority=10, hooks={"before_load": before_load})


# Module-level instance so ``plugins = ["epresso_blog"]`` auto-discovers it.
blog = epresso_blog()
