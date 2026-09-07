"""Markdown link resolution — map link targets to site URLs.

Supports GitHub/wiki-style link syntax:

* ``[Label](Page)`` / ``[Label](Page.md)`` — relative links resolved to a URL
* ``[Label](/path)``                       — absolute paths (passed through)
* ``[[Page]]`` / ``[[Page|Label]]``        — wiki links
* ``[wiki_page:Page]``                     — wiki page reference
* external URLs, ``#anchors`` and ``mailto:`` — passed through unchanged

A :class:`LinkResolver` holds a map of names (content ids, slugs, and lowercased
titles) to URLs, built from the site's routes. Unresolvable targets return
``None`` so callers can leave them as written.
"""

from __future__ import annotations

_EXTENSIONS = (".md", ".markdown", ".mdx")


def _strip_md_ext(name: str) -> str:
    """Strip a trailing markdown extension: ``Page.md`` -> ``Page``."""
    for ext in _EXTENSIONS:
        if name.lower().endswith(ext):
            return name[: -len(ext)]
    return name


class LinkResolver:
    """Resolve a link target (page name, slug, or ``.md`` path) to a site URL."""

    def __init__(self) -> None:
        self._urls: dict[str, str] = {}

    def add_name(self, name: str, url: str) -> None:
        """Map ``name`` (a page id/slug/title) to ``url`` (case-insensitive)."""
        name = (name or "").strip().lower()
        if name:
            self._urls[name] = url

    def resolve(self, target: str) -> str | None:
        """Resolve ``target`` to a URL, or ``None`` if it can't be resolved."""
        t = (target or "").strip()
        if not t:
            return None
        # External / protocol-relative / mailto / anchor / data — pass through.
        if "://" in t or t.startswith(("//", "#", "mailto:", "data:")):
            return t
        # Absolute path. Leave route URLs and assets alone, but rewrite a
        # markdown ``.md``/``.markdown``/``.mdx`` link to its page URL so e.g.
        # ``/docs/foo.md`` becomes ``/docs/foo/``. Unresolvable ones stay as-is.
        if t.startswith("/"):
            name, _, frag = t.partition("#")
            stripped = _strip_md_ext(name)
            if stripped == name:  # not a markdown link
                return t
            url = self._urls.get(stripped) or self._urls.get(stripped + "/")
            if url is not None:
                return url + (f"#{frag}" if frag else "")
            return t
        # Split off an optional #fragment, strip ./ and trailing slash.
        name, _, frag = t.partition("#")
        name = name.lstrip("./").rstrip("/")
        # Strip a markdown extension: Page.md -> Page
        name = _strip_md_ext(name)
        url = self._urls.get(name.lower())
        if url is None:
            return None
        return url + (f"#{frag}" if frag else "")
