"""Generated outputs — sitemap.xml, robots.txt, 404.html, search-index.json.

These are built-in (opt-out via config), generated at the end of a build so they
always exist even for a minimal site. They are skipped when the user has already
produced them via an endpoint/pages file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _site_url(site: Any) -> str:
    return (site.config.site.url or "http://localhost:8000").rstrip("/")


def _is_html_page(path: str) -> bool:
    return path == "/" or path.endswith("/")


def write_sitemap(site: Any, out_dir: Path, routes: list[Any]) -> None:
    if not site.config.seo.sitemap:
        return
    from html import escape as _h

    out = out_dir / "sitemap.xml"
    if out.exists():
        return  # user provided their own
    urls = [
        f"<url><loc>{_h(_site_url(site) + r.path)}</loc></url>"
        for r in routes
        if _is_html_page(r.path) and not r.path.startswith("/404")
    ]
    out.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n",
        encoding="utf-8",
    )


def write_robots(site: Any, out_dir: Path) -> None:
    if not site.config.seo.robots:
        return
    out = out_dir / "robots.txt"
    if out.exists():
        return  # user provided their own
    lines = ["User-agent: *", "Allow: /"]
    if site.config.seo.sitemap and site.config.site.url:
        lines.append(f"Sitemap: {_site_url(site)}/sitemap.xml")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _route_title_description(route: Any) -> tuple[str, str]:
    """Best-effort ``(title, description)`` for a page route."""
    data = getattr(route, "data", None)
    # Content entries wrap the front-matter model in ``.data``.
    if data is not None and not isinstance(data, dict) and hasattr(data, "data"):
        data = data.data

    def _get(obj: Any, key: str) -> str:
        value = obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)
        return " ".join(str(value).split()) if value else ""

    title = _get(data, "title")
    description = _get(data, "description") or _get(data, "summary")
    fm = getattr(route, "frontmatter", None)
    if isinstance(fm, dict):
        title = title or _get(fm, "title")
        description = description or _get(fm, "description") or _get(fm, "summary")
    # Direct Markdown pages keep their front-matter on disk.
    source = getattr(route, "source", None)
    if not title and source is not None and source.suffix.lower() == ".md":
        try:
            from .document import parse_document

            md = parse_document(source.read_text(encoding="utf-8"), "markdown").data or {}
            title = _get(md, "title")
            description = description or _get(md, "description") or _get(md, "summary")
        except OSError:
            pass
    return title, description


def _section_title(segment: str) -> str:
    return segment.replace("-", " ").replace("_", " ").strip().title()


def write_llms(site: Any, out_dir: Path, routes: list[Any]) -> None:
    """Generate ``llms.txt`` (https://llmstxt.org/) from page routes.

    An H1 site title and blockquote summary, then one bullet per page grouped by
    its top-level path segment. Skipped when the user has provided their own.
    """
    cfg = site.config.seo.llms
    if not cfg.enabled:
        return
    out = out_dir / cfg.path.lstrip("/")
    if out.exists():
        return  # user provided their own
    title = cfg.title or site.config.site.name or "Site"
    description = " ".join((cfg.description or site.config.site.description or "").split())
    base = _site_url(site)

    pages = [
        r
        for r in routes
        if _is_html_page(r.path) and not r.path.startswith("/404") and not r.redirect_to
    ]

    def _line(route: Any) -> str:
        r_title, r_desc = _route_title_description(route)
        if not r_title:
            leaf = route.path.strip("/").split("/")[-1]
            r_title = _section_title(leaf) if leaf else "Home"
        label = r_title.replace("[", "\\[").replace("]", "\\]")
        text = f"- [{label}]({base + route.path})"
        if r_desc:
            text += f": {r_desc}"
        return text

    root: list[Any] = []
    groups: dict[str, list[Any]] = {}
    for r in pages:
        seg = r.path.strip("/").split("/")[0] if r.path != "/" else ""
        (root if not seg else groups.setdefault(seg, [])).append(r)

    lines = [f"# {title}", ""]
    if description:
        lines += [f"> {description}", ""]
    if root:
        lines += [_line(r) for r in root]
        lines.append("")
    for seg, group in groups.items():
        lines += [f"## {_section_title(seg)}", ""]
        lines += [_line(r) for r in group]
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_404(site: Any, out_dir: Path, routes: list[Any]) -> None:
    if (out_dir / "404.html").exists():
        return
    # if the user has a pages/404 route, promote its output to 404.html
    for r in routes:
        if r.path == "/404/":
            src = out_dir / "404" / "index.html"
            if src.exists():
                import shutil

                shutil.copyfile(src, out_dir / "404.html")
            return
    out_dir.joinpath("404.html").write_text(
        "<!doctype html><html><head><title>404</title></head>"
        "<body><h1>404 — Not Found</h1><p><a href=\"/\">Home</a></p></body></html>\n",
        encoding="utf-8",
    )


def rss_feed(site: Any, *, title: str, description: str, path: str, items: list[dict[str, Any]]) -> str:
    """Return an Atom/RSS 2.0 XML feed string (usable in an endpoint).

    ``items``: list of ``{"title", "url", "date", "summary"}``.
    """
    import datetime
    import email.utils
    from html import escape as _h

    base = _site_url(site)

    def _e(s):  # escape XML element content (& < >)
        return _h("" if s is None else str(s), quote=False)

    def _ea(s):  # escape XML attribute value (also " ')
        return _h("" if s is None else str(s), quote=True)

    def date_str(d: Any) -> str:
        if isinstance(d, str):
            d = d.replace("Z", "+00:00")
            try:
                dt = datetime.datetime.fromisoformat(d)
            except ValueError:
                return _e(d)
            return email.utils.format_datetime(dt)
        if isinstance(d, datetime.datetime):
            return email.utils.format_datetime(d)
        return ""

    entries = []
    for it in items:
        link = it["url"] if it["url"].startswith("http") else base + it["url"]
        entries.append(
            "<item>"
            f"<title>{_e(it.get('title', ''))}</title>"
            f"<link>{_e(link)}</link>"
            f"<guid>{_e(link)}</guid>"
            f"<pubDate>{_e(date_str(it.get('date')))}</pubDate>"
            f"<description>{_e(it.get('summary', ''))}</description>"
            "</item>"
        )
    feed_url = base + path
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        f"<title>{_e(title)}</title>"
        f"<link>{_e(base)}</link>"
        f"<description>{_e(description)}</description>"
        f"<atom:link href=\"{_ea(feed_url)}\" rel=\"self\" type=\"application/rss+xml\" xmlns:atom=\"http://www.w3.org/2005/Atom\"/>"
        + "\n".join(entries)
        + "</channel></rss>\n"
    )


def write_rss(site: Any, out_dir: Path, routes: list[Any]) -> None:
    """Generate an RSS feed from a content collection when ``[seo] rss`` is enabled.

    Each entry's title/date/description are read from its data (falling back to
    the entry id for the title); the URL comes from ``url_template``.
    """
    cfg = site.config.seo.rss
    if not cfg.enabled or not cfg.collection:
        return
    collection = site.get_collection(cfg.collection)
    if not collection:
        return

    items: list[dict[str, Any]] = []
    for e in collection:
        data = e.data
        title = getattr(data, "title", None) or e.id
        url = cfg.url_template.format(collection=cfg.collection, id=e.id)
        date = getattr(data, "date", None) or ""
        summary = getattr(data, "description", None) or ""
        items.append({"title": title, "url": url, "date": date, "summary": summary})
    if cfg.limit and cfg.limit > 0:
        items = items[: cfg.limit]

    path = cfg.path or "/rss.xml"
    xml = rss_feed(
        site,
        title=cfg.title or site.config.site.name,
        description=cfg.description or site.config.site.description,
        path=path,
        items=items,
    )
    out = out_dir / path.lstrip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(xml, encoding="utf-8")


def write_search_index(site: Any, out_dir: Path, routes: list[Any], rendered: dict[str, str]) -> None:
    """Build a BM-25 search index (core, no lunr) over page sections."""
    if not site.config.search.enabled:
        return
    from . import search

    units: list[dict[str, Any]] = []
    for r in routes:
        if not _is_html_page(r.path):
            continue
        html = rendered.get(r.path)
        if html is None:
            continue
        units.extend(search.split_sections(html, r.path))

    out = out_dir / site.config.search.index
    if not units:
        out.write_text("{}", encoding="utf-8")
        return
    out.write_text(search.serialize(search.build_index(units)), encoding="utf-8")
