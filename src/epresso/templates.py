"""Template engine — Jinja2 with curated globals and no arbitrary Python."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from jinja2 import ChoiceLoader, Environment, FileSystemLoader
from jinja2 import TemplateError as JinjaError
from markupsafe import Markup

from .components import install as install_components
from .document import strip_frontmatter
from .errors import TemplateError
from .jsx import JsxTagsExtension
from .markdown import pygments_css, pygments_css_pair


class EpressoFileSystemLoader(FileSystemLoader):
    """FileSystemLoader that strips ``--- ... ---`` Python frontmatter from
    ``.ep`` files before Jinja parses them, so a component or layout body is
    loaded as plain Jinja (the delimiter would otherwise render as literal
    text).
    """

    def get_source(self, environment: Any, template: str):
        contents, filename, uptodate = super().get_source(environment, template)
        if filename and filename.endswith(".ep"):
            contents = strip_frontmatter(contents)
        return contents, filename, uptodate


def build_environment(config: Any, pages_dir: Path | None = None, extra_roots: Sequence[Path] = ()) -> Environment:
    """Build the Jinja environment from ``layouts/`` and ``components/``.

    ``pages/`` is added so pages can be used as templates / extend layouts.
    ``extra_roots`` are external layers appended *after* the site's own roots, so
    the site always wins (see :mod:`epresso.layers`).
    """
    roots = [config.dir_layouts(), config.dir_components()]
    roots.extend(extra_roots)
    loaders = [EpressoFileSystemLoader(str(d)) for d in _dedupe(roots) if d.exists()]
    if pages_dir and pages_dir.exists():
        loaders.append(EpressoFileSystemLoader(str(pages_dir)))
    env = Environment(
        loader=ChoiceLoader(loaders) if len(loaders) > 1 else (loaders[0] if loaders else None),
        autoescape=True,
        keep_trailing_newline=True,
    )
    install_components(env)
    env.add_extension(JsxTagsExtension)
    return env


def _dedupe(paths: Sequence[Path]) -> list[Path]:
    """Paths in order, dropping repeats (resolved) so a layer can't shadow itself."""
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        key = p.resolve()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


class CuratedGlobals:
    """Functions/values we intentionally expose to templates. Nothing else."""

    def __init__(self, site: Any) -> None:
        self._site = site

    def url(self, path: str) -> str:
        """Normalize an internal path to a URL (respect trailing-slash policy)."""
        if not path:
            return "/"
        trailing = self._site.config.build.trailing_slash
        if path == "/":
            return path
        last = path.rstrip("/").split("/")[-1]
        is_file = "." in last
        if is_file:
            return "/" + path.lstrip("/")
        path = "/" + path.strip("/")
        if trailing == "always" and path != "/":
            return path + "/"
        return path

    def asset(self, name: str) -> str:
        """Resolve an asset to its content-hashed public URL (v1.5)."""
        return self._site.assets.resolve(name)

    def image(self, name: str, widths: list[int] | None = None, alt: str = "") -> str:
        """Render a responsive <img> (WebP srcset) from a source image."""
        from markupsafe import Markup

        return Markup(self._site.images.render(name, widths, alt))

    def picture(self, name: str, widths: list[int] | None = None, alt: str = "") -> str:
        """Render a responsive <picture> (WebP sources + JPEG fallback)."""
        from markupsafe import Markup

        return Markup(self._site.images.picture(name, widths, alt))

    def seo(
        self,
        title: str | None = None,
        description: str | None = None,
        image: str | None = None,
        path: str = "/",
        og_type: str = "website",
    ) -> str:
        """Render standard <meta> / Open Graph / Twitter head tags."""
        from markupsafe import Markup

        site = self._site
        name = title or site.config.site.name
        desc = description or site.config.site.description
        url = site.config.site.url.rstrip("/") + (path if path.startswith("/") else "/" + path)
        tags = [
            f"<title>{name}</title>",
            '<meta charset="utf-8">',
            f'<meta name="description" content="{desc}">' if desc else "",
            f'<link rel="canonical" href="{url}">',
            f'<meta property="og:title" content="{name}">',
            f'<meta property="og:type" content="{og_type}">',
            f'<meta property="og:url" content="{url}">',
            f'<meta property="og:description" content="{desc}">' if desc else "",
            f'<meta property="og:image" content="{image}">' if image else "",
            f'<meta name="twitter:card" content="{"summary_large_image" if image else "summary"}">',
            f'<meta name="twitter:title" content="{name}">',
            f'<meta name="twitter:description" content="{desc}">' if desc else "",
            f'<meta name="twitter:image" content="{image}">' if image else "",
        ]
        return Markup("\n".join(t for t in tags if t))

    def get_collection(self, name: str) -> list[Any]:
        return self._site.get_collection(name)

    def get_entry(self, collection: str, entry_id: str) -> Any:
        return self._site.get_entry(collection, entry_id)

    def render_md(self, body: str) -> Markup:
        """Render a Markdown string to safe HTML (used by components for prose
        content stored in frontmatter, e.g. card bodies with links)."""
        from markupsafe import Markup as _M

        from .markdown import render_markdown

        return _M(render_markdown(body, self._site.config.markdown).html)

    def fmt_dt(self, iso: str, fmt: str = "%H:%M 'on' %A, %d %B %Y") -> str:
        """Format an ISO datetime string (parsed as-is, its own offset) for display."""
        from datetime import datetime as _dt

        try:
            return _dt.fromisoformat(iso).strftime(fmt)
        except Exception:
            return iso or ""

    def expand_md_components(self, html: str, page_data: dict[str, Any] | None = None) -> Markup:
        """Expand markdown component placeholders into epresso component output.

        The markdown renderer emits ``<!--epresso-md:{name,props}-->children``
        placeholders for allow-listed tags (e.g. ``<Button url="…">…</Button>``).
        This expands them via the component system at template time (env ready).
        ``page_data`` (optional) is the page's frontmatter, exposed to components
        as ``md_page_data()`` so markdown components can read page content data
        (e.g. ``TriviaCarousel`` reading ``trivia`` from the frontmatter).
        """

        from markupsafe import Markup as _M

        from .components import _render_component
        from .markdown import expand_placeholders

        if page_data is not None:
            self._site._md_page_data = page_data

        def _repl(name: str, props: dict[str, Any], children: str) -> str:
            try:
                return _render_component(self._site.env, name, _M(children), props)
            except Exception:  # noqa: BLE001 — unknown component -> keep children
                return children

        return _M(expand_placeholders(html, _repl))

    def md_page_data(self) -> dict[str, Any]:
        """Return the current page's frontmatter (set by expand_md_components)."""
        return getattr(self._site, "_md_page_data", {}) or {}

    def highlight_title(self, text: str, highlight: str = "", color: str = "") -> Markup:
        """Split ``text`` at ``highlight`` (case-insensitive) and wrap the match
        in a colored span, inserting a ``<br>`` before/after (title parity).
        Returns the original text unchanged if ``highlight`` is empty/absent.
        """

        if not highlight:
            return Markup(text)
        idx = text.upper().find(highlight.upper())
        if idx == -1:
            return Markup(text)
        c = color or "var(--color-accent)"
        before = text[:idx].rstrip()
        match = text[idx : idx + len(highlight)]
        after = text[idx + len(highlight) :]
        if not before:
            return Markup(f'<span style="color: {c}">{match}</span><br>{after.lstrip()}')
        return Markup(f'{before}<br><span style="color: {c}">{match}</span>{after}')


def bind_globals(env: Environment, site: Any) -> None:
    from . import __version__  # local import: the package is fully loaded by now
    from .classes import cn
    from .variants import Variant, VariantProps, resolve_variants, spread

    g = CuratedGlobals(site)
    env.globals.update(
        {
            "site": site,
            "cn": cn,
            "Variant": Variant,
            "VariantProps": VariantProps,
            "resolve_variants": resolve_variants,
            "spread": spread,  # renders `props.attrs` as attributes
            "_render_session": site.session,  # side-band render output (scoped CSS + scripts)
            "url": g.url,
            "epresso_version": __version__,
            "asset": g.asset,
            "image": g.image,
            "picture": g.picture,
            "seo": g.seo,
            "render_md": g.render_md,
            "fmt_dt": g.fmt_dt,
            "get_collection": g.get_collection,
            "get_entry": g.get_entry,
            "expand_md_components": g.expand_md_components,
            "md_page_data": g.md_page_data,
            "highlight_title": g.highlight_title,
            "pygments_css": lambda theme="default", selector=".highlight": Markup(pygments_css(theme, selector)),
            "pygments_css_pair": lambda light="default", dark="default", selector=".highlight": Markup(
                pygments_css_pair(light, dark, selector)
            ),
            "env": site.env_name,
            "env_vars": site.env_vars,
        }
    )


def _layout_component_name(layout: str) -> str:
    """Normalize a front-matter ``layout:`` value to a component name.

    Accepts ``Base``, ``Base.ep``, ``layouts/Base`` and ``layouts/Base.ep``.
    """
    name = layout.strip()
    if name.lower().endswith(".html"):
        raise TemplateError(
            f"layout {layout!r}: .html layouts are not supported",
            fix="use a layout component — a layouts/<Name>.ep file with <slot/>, referenced as `layout: <Name>`",
        )
    if name.endswith(".ep"):
        name = name[:-3]
    for prefix in ("layouts/", "components/"):
        if name.startswith(prefix):
            name = name[len(prefix) :]
    return name


def render_markdown_page(
    env: Environment,
    *,
    title: str,
    content_html: str,
    frontmatter: dict[str, Any],
    layout: str | None,
    site: Any,
    route_path: str,
) -> str:
    """Render a direct Markdown page, wrapping content in the front-matter layout.

    A layout is a **layout component** (``.ep``). Its title is passed both as a
    ``title`` prop and as a ``slot="title"`` fragment, and the rendered Markdown
    is the default slot.
    """
    ctx: dict[str, Any] = {
        "site": site,
        "page": {**frontmatter, "title": title},
        "params": {},
        "props": {},
        "route": {"path": route_path},
        "content": Markup(content_html),
    }
    if layout:
        name = _layout_component_name(layout)
        child_src = (
            "{% component " + repr(name) + ", title=page.title %}"
            '<Fragment slot="title">{{ page.title }}</Fragment>'
            "{{ content | safe }}"
            "{% endcomponent %}"
        )
        child = env.from_string(child_src)
        try:
            from .components import unwrap_fragments

            return unwrap_fragments(child.render(**ctx))
        except JinjaError as e:
            raise TemplateError(f"error rendering layout {layout!r}: {e}") from e
    # No layout: emit a minimal standalone HTML document.
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title></head><body>{content_html}</body></html>"
    )
