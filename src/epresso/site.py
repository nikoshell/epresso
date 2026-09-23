"""epresso Site — the Python API. ``Site.load(root).build()``.

Orchestrates: config → content collections → markdown render → routes →
template render → write ``dist/``. Deterministic + incremental-aware.
"""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import outputs
from .assets import AssetPipeline
from .config import Config, load_config
from .content import ContentStore, load_collections
from .content.store import RenderedContent
from .document import parse_document
from .images import ImagePipeline
from .incremental import BuildGraph, RenderedBodyCache
from .layers import Layer, resolve_layers
from .logger import get_logger
from .markdown import render_markdown
from .plugins import PluginManager
from .render import RenderSession
from .routing import Route, RouteError, discover_route_patterns, expand_pattern, output_path_for
from .templates import bind_globals, build_environment, render_markdown_page

__all__ = ["Site", "BuildResult"]

_log_render = get_logger("render")
_log_content = get_logger("content")


@dataclass
class BuildResult:
    pages: list[str] = field(default_factory=list)
    endpoints: list[str] = field(default_factory=list)
    collections: int = 0
    entries: int = 0
    duration: float = 0.0
    skipped: int = 0
    asset_warnings: list[str] = field(default_factory=list)
    perf: dict[str, float] = field(default_factory=dict)  # phase -> seconds


def _is_entry(obj: Any) -> bool:
    return hasattr(obj, "data") and hasattr(obj, "rendered") and not isinstance(obj, dict)


def _entry_content(obj: Any) -> str | None:
    if _is_entry(obj) and obj.rendered:
        return obj.rendered.html
    return None


class Site:
    """A epresso site. The core domain object and the data API."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.store = ContentStore()
        self.env = None  # Jinja2 environment (set in _do_load)
        self.env_name: str | None = None  # active environment name, e.g. 'production'
        self.env_vars: dict[str, str] = {}  # vars from .env.<env>
        self.assets = AssetPipeline(config)
        self.images = ImagePipeline(config)
        self.plugins = PluginManager()
        self.plugins.discover(config.root, config)
        # html transforms contributed by plugins via ``caps.transform_html``; reset
        # each load so re-loads are idempotent.
        self._html_transforms: list[tuple[str, Any]] = []
        # source transforms contributed via ``caps.add_source_transform``; reset
        # each load for the same reason (``on_setup`` re-registers them).
        self._source_transforms: list[tuple[str, Any]] = []
        self._production = False  # True during production builds (hides drafts/scheduled)
        self._loaded = False
        self._link_resolver = None  # lazily built from routes/content
        # Content dependency tracking + the incremental cache live in the build
        # graph, not on Site — see BuildGraph.
        self.graph = BuildGraph(self.store, self.config)
        self.layers: list[Layer] = []  # resolved [layers] roots (populated in _do_load)
        self._perf: dict[str, float] = {}  # load-phase timings, surfaced by BuildResult.perf
        self._route_metadata: dict[str, Any] = {}
        self._page_templates: dict[str, Any] = {}  # template_str -> compiled page template
        self._routes: list[Route] | None = None  # cached route expansion; cleared by _do_load
        # Side-band render output (scoped CSS + client scripts) lives in the
        # render session, not on Site — see RenderSession.
        self.session = RenderSession()

    # -- data API (exposed to get_static_paths sidecars and templates) ------
    def get_collection(self, name: str) -> list[Any]:
        self.graph.record_dependency(f"collection:{name}")
        entries = self.store.get_collection(name)
        return [e for e in entries if self._is_published(e)]

    def get_entry(self, collection: str, entry_id: str) -> Any:
        self.graph.record_dependency(f"{collection}:{entry_id}")
        return self.store.get_entry(collection, entry_id)

    def get_entries(self, collection: str, entry_ids: list[str]) -> list[Any]:
        """Resolve content references (``reference()``), recording dependency edges."""
        from .errors import ContentError

        out: list[Any] = []
        for eid in entry_ids:
            entry = self.get_entry(collection, eid)
            if entry is None:
                raise ContentError(f"unknown content reference {collection}:{eid!r}")
            out.append(entry)
        return out

    def get_tags(self, collection: str, field: str = "tags") -> dict[str, list[Any]]:
        """Group a collection's entries by a tag/category field."""
        tags: dict[str, list[Any]] = {}
        for e in self.get_collection(collection):
            data = e.data
            vals = data.get(field) if isinstance(data, dict) else getattr(data, field, None)
            for t in vals or []:
                tags.setdefault(str(t), []).append(e)
        return tags

    def rss(self, *, title: str, description: str, path: str, items: list[dict]) -> str:
        """Build an RSS/Atom feed string (for use in an endpoint)."""
        return outputs.rss_feed(self, title=title, description=description, path=path, items=items)

    def _include_status(self, status: str) -> bool:
        """Whether entries of ``status`` (``"draft"``/``"private"``) are included in
        this build. An explicit config bool wins; otherwise fall back to the
        historic default: shown outside production, hidden in production."""
        key = "show_drafts" if status == "draft" else "show_private"
        cfg = getattr(self.config.content, key, None)
        if cfg is not None:
            return bool(cfg)
        return not self._production

    def _is_published(self, entry: Any) -> bool:
        data = entry.data

        def get(k: str):
            return data.get(k) if isinstance(data, dict) else getattr(data, k, None)

        # Draft/private visibility is configurable per environment.
        if get("draft") and not self._include_status("draft"):
            return False
        if get("private") and not self._include_status("private"):
            return False
        # Future-scheduled entries are hidden only in production (they stay
        # visible while previewing in development/preview).
        if not self._production:
            return True
        for f in ("date", "published_at", "published", "date_published"):
            v = get(f)
            if isinstance(v, str):
                try:
                    import datetime

                    d = datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
                    if d.tzinfo is None:
                        d = d.replace(tzinfo=datetime.UTC)
                    now = datetime.datetime.now(datetime.UTC)
                    if d > now:
                        return False  # scheduled for the future
                except ValueError:
                    pass
        return True

    # -- loading ------------------------------------------------------------
    @classmethod
    def load(cls, root: Path | None = None, env: str | None = None, *, load: bool = True, dev: bool = False) -> Site:
        """Load a site. ``env`` selects ``site.<env>.toml`` + ``.env.<env>``.

        ``load=False`` defers the content load to :meth:`build`, for callers that
        are about to build anyway. Without it every collection is loaded and every
        Markdown body rendered twice (once here, once in ``build``).

        ``dev=True`` serves unhashed asset URLs. It must be applied here rather
        than after loading: the rendered-body cache is keyed on the config hash, so
        flipping ``assets.hash`` afterwards invalidates every cached body.
        """
        import os

        from .config import load_env_file

        env = env or os.environ.get("EPRESSO_ENV")
        config = load_config(root, env=env)
        if dev:
            config.assets.hash = False
        site = cls(config)
        site.env_name = env
        site.env_vars = load_env_file(config.root, env)
        # expose env vars to os.environ for content loaders / plugins (do not override)
        for k, v in site.env_vars.items():
            os.environ.setdefault(k, v)
        if load:
            site._do_load()
        return site

    def _do_load(self) -> None:
        self.store = ContentStore()  # idempotent reload: recreate the store
        self.layers = resolve_layers(self.config)  # external component/layout roots
        layer_dirs = [layer.root for layer in self.layers]
        self.graph = BuildGraph(self.store, self.config, layer_dirs)  # fresh graph + cache per load
        self.assets = AssetPipeline(self.config)  # fresh reference map per load
        self.images = ImagePipeline(self.config)  # fresh transform map per load
        self._link_resolver = None  # rebuild from fresh routes on (re)load
        self._html_transforms = []  # idempotent: plugin transforms re-register each load
        self._source_transforms = []  # likewise; they are per-environment too
        self._page_templates = {}  # fresh Jinja environment => compiled page templates are stale
        self._routes = None  # routes hold the previous load's entries
        self.plugins.run_hook("before_load", self)
        # Phase timings for `epresso build --perf` and bench/run.py; cheap enough
        # to always collect (two perf_counter pairs per load).
        self._perf = {}
        _t = time.monotonic()
        load_collections(self.store, self.config.root)
        self._perf["collections"] = time.monotonic() - _t
        _t = time.monotonic()
        self._render_content_bodies()
        self._perf["content"] = time.monotonic() - _t
        # Rendering bodies expands routes on the way (the link resolver), before
        # every entry has one — that expansion is incomplete, so drop it.
        self._routes = None
        _t = time.monotonic()
        self.env = build_environment(self.config, self.config.dir_pages(), layer_dirs)
        bind_globals(self.env, self)
        self.plugins.run_hook("on_setup", self)  # globals/filters/transforms (also used in dev)
        self.plugins.run_hook("after_load", self)
        self._perf["setup"] = time.monotonic() - _t
        self._loaded = True

    def _render_content_bodies(self) -> None:
        content_dir = self.config.dir_content()
        component_names = tuple(self.config.markdown.components or [])
        from .markdown import component_placeholder

        # Reuse persisted bodies for unchanged entries: the cache is keyed by entry
        # digest and gated by the same config/code hashes as the incremental
        # manifest. A body is a pure function of its digest, so this is correct for
        # every caller — the dev reload as much as the build.
        config_hash, code_hash = self.graph.ensure_hashes()
        cache = RenderedBodyCache(self.config.cache_dir())
        cached = cache.load(config_hash, code_hash)

        for name in self.store.names():
            for entry in self.store.get_collection(name):
                _log_content.debug(f"render body {name}:{entry.id}")
                image_base = None
                # Relative markdown images resolve against the source content
                # dir, mirrored under public/content/<rel> (EP convention).
                if entry.file_path and content_dir in entry.file_path.parents:
                    rel = entry.file_path.parent.relative_to(content_dir)
                    image_base = "/content/" + rel.as_posix() + "/"
                # image_base is not part of the entry digest, so fold it into the
                # cache key (identical bodies in different dirs render differently).
                cache_key = f"{entry.digest}:{image_base or ''}" if entry.digest else ""
                hit = cached.get(cache_key) if cache_key else None
                if hit is not None:
                    entry.rendered = RenderedContent(
                        html=hit.get("html", ""), metadata=hit.get("metadata", {})
                    )
                    continue
                entry.rendered = render_markdown(
                    entry.body or "",
                    self.config.markdown,
                    image_base=image_base,
                    component_names=component_names,
                    component_renderer=component_placeholder if component_names else None,
                    link_resolver=self.link_resolver(),
                )
                if cache is not None and cache_key:
                    cached[cache_key] = {
                        "html": entry.rendered.html,
                        "metadata": entry.rendered.metadata,
                    }

        cache.store(config_hash, code_hash, cached)

    # -- link resolution ----------------------------------------------------
    def link_resolver(self) -> Any:
        """A :class:`LinkResolver` mapping content names/slugs/titles to URLs."""
        if self._link_resolver is None:
            from .links import LinkResolver

            resolver = LinkResolver()
            for route in self.resolve_routes():
                resolver.add_name(route.path, route.path)
                if _is_entry(route.data):
                    entry = route.data
                    resolver.add_name(entry.id, route.path)
                    # Register the file basename so sibling-relative links like
                    # ``./styling`` resolve even when they don't match a title.
                    base = entry.id.rstrip("/").split("/")[-1]
                    if base:
                        resolver.add_name(base, route.path)
                    title = getattr(entry.data, "title", None)
                    if title:
                        resolver.add_name(str(title), route.path)
            self._link_resolver = resolver
        return self._link_resolver

    # -- build --------------------------------------------------------------
    def resolve_routes(self) -> list[Route]:
        """Expand all pages/ patterns into concrete routes (deterministic order).

        Cached for the life of a load: the dev server asks several times per
        request, and each expansion walks every page and runs
        ``get_static_paths()``. ``_do_load`` clears it.
        """
        if self.graph.expanding:
            raise RouteError("resolve_routes() called during route resolution (recursive endpoint?)")
        if self._routes is not None:
            return self._routes
        patterns = discover_route_patterns(self.config.dir_pages())
        routes: list[Route] = []
        if self.config.build.redirects:
            from .routing import redirect_routes

            routes.extend(redirect_routes(self.config))
        self.graph.begin_expand()
        for pattern in patterns:
            for r in expand_pattern(pattern, self.config.build.trailing_slash, self):
                routes.append(r)
        self.graph.end_expand()
        # Deduplicate by path, keep first, deterministic.
        seen: set[str] = set()
        dedup: list[Route] = []
        for r in routes:
            if r.path not in seen:
                seen.add(r.path)
                dedup.append(r)
        dedup.sort(key=lambda r: r.path)
        self._routes = dedup
        return dedup

    def _page_template(self, source: str, path: str = "") -> Any:
        """Compile a page's ``template_str`` once per load.

        Every route fanned out by one ``get_static_paths()`` shares the same
        template string, so without this the same page was compiled once per
        route. Keyed on the source, so an edited template is a new entry.

        ``path`` is passed through to plugin source transforms for context only;
        the cache key stays the original source so fan-out still hits it.
        """
        tmpl = self._page_templates.get(source)
        if tmpl is None:
            body = self._apply_source_transforms(source, kind="page", path=path)
            tmpl = self.env.from_string(body)
            self._page_templates[source] = tmpl
        return tmpl

    def render_route(self, route: Route) -> tuple[str, str] | None:
        """Render one route → (content, content_type). None if nothing to write."""
        assert self.env is not None, "site not loaded"
        self.graph.begin_route(route.path)
        self.session.begin_render()
        try:
            if route.body is not None:
                # endpoint
                return route.body, route.content_type
            if route.template_str:
                # If the route's data is a content Entry, surface front matter as
                # ``props`` and rendered Markdown as ``content``.
                from markupsafe import Markup

                entry_data = route.data.data if _is_entry(route.data) else route.data
                rendered_html = _entry_content(route.data)
                ctx: dict[str, Any] = {
                    "site": self,
                    "params": route.params,
                    "props": entry_data if entry_data is not None else {},
                    "data": entry_data if entry_data is not None else {},
                    "route": {"path": route.path},
                }
                if rendered_html is not None:
                    ctx["content"] = Markup(rendered_html)
                if route.frontmatter:
                    ctx.update(route.frontmatter)
                if route.template_str:
                    page_path = str(route.source) if route.source else ""
                    html = self._page_template(route.template_str, page_path).render(**ctx)
                else:
                    html = ""
                if route.scoped_css:
                    from .scoped import inject_scope_attr

                    scope = route.scope_hash
                    self.session.add_scoped_css(scope, route.scoped_css)
                    html = inject_scope_attr(html, scope)
                if route.scripts:
                    self.session.add_script(route.scripts)
                html = self._apply_html_transforms(route, html)
                return html, "text/html"
            if route.source and route.source.suffix.lower() == ".md":
                return self._render_direct_md(route)
            return None
        finally:
            self.graph.end_route()

    def _render_direct_md(self, route: Route) -> tuple[str, str]:
        assert self.env is not None
        assert route.source is not None
        raw = route.source.read_text(encoding="utf-8")
        doc = parse_document(raw, "markdown")
        frontmatter, body = doc.data or {}, doc.body
        title = frontmatter.get("title", "Untitled")
        rendered = render_markdown(body, self.config.markdown)
        layout = frontmatter.get("layout") or self.config.markdown.default_layout
        html = render_markdown_page(
            self.env,
            title=str(title),
            content_html=rendered.html,
            frontmatter=frontmatter,
            layout=layout,
            site=self,
            route_path=route.path,
        )
        html = self._apply_html_transforms(route, html)
        return html, "text/html"

    def _apply_source_transforms(self, source: str, *, kind: str, path: str) -> str:
        """Run plugin-contributed source transforms over a template body.

        Applied at the point a ``.ep`` body becomes a Jinja template and *before*
        epresso's own body rewriting (slot expansion in ``components``, JSX tag
        rewriting by ``jsx``), so a transform sees the body as the author wrote
        it rather than a half-desugared one.

        ``kind`` is ``"page"`` or ``"component"`` — layouts are components (tell
        them apart by ``path``); ``path`` is the file being compiled. Transforms
        may change what a page renders, so a registered transform disables
        per-route output reuse (see ``build``).
        """
        if not self._source_transforms:
            return source
        ctx: dict[str, Any] = {"kind": kind, "path": path}
        for _name, fn in self._source_transforms:
            source = fn(source, ctx)
        return source

    def _apply_html_transforms(self, route: Route, html: str) -> str:
        """Run plugin-contributed html transforms over a rendered page.

        Transforms are applied at render time (build + dev) so a fresh render
        and an incremental render agree. Because a transform could depend on the
        plugin's own code (not just content), any registered transform disables
        per-route output reuse (see ``build``) — content-body caching still holds.
        """
        if not self._html_transforms:
            return html
        ctx: dict[str, Any] = {"path": route.path, "params": route.params}
        for _name, fn in self._html_transforms:
            html = fn(html, ctx)
        return html

    def _apply_base_prefix(self, out_dir: Path) -> None:
        """Prefix root-relative URLs with ``[build] base`` in built output.

        Only runs when ``base`` is set (project Pages e.g. "/epresso/"). Rewrites
        emitted HTML (href/src) and CSS (url()) so a project-Pages site resolves
        its assets/scripts. Dev is unaffected (it serves at the root).
        """
        import re

        base = (self.config.build.base or "").strip().strip("/")
        if not base:
            return
        base = "/" + base + "/"
        base_js = base.rstrip("/")
        html_re = re.compile(r'((?:href|src)=["\'])/(?!/)')
        css_re = re.compile(r"(url\([\"\']?)/(?!/)")
        for f in out_dir.rglob("*"):
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            if ext == ".html":
                s = f.read_text(encoding="utf-8", errors="replace")
                ns = html_re.sub(lambda m: m.group(1) + base, s)
                # Let client scripts resolve root-relative data URLs under the base.
                if "EPRESSO_BASE" not in ns and "</head>" in ns:
                    ns = ns.replace(
                        "</head>",
                        f'<script>window.EPRESSO_BASE={base_js!r};</script></head>',
                        1,
                    )
                if ns != s:
                    f.write_text(ns, encoding="utf-8")
            elif ext == ".css":
                s = f.read_text(encoding="utf-8", errors="replace")
                ns = css_re.sub(lambda m: m.group(1) + base, s)
                if ns != s:
                    f.write_text(ns, encoding="utf-8")

    def build(self, *, clean: bool = True, progress: Any | None = None) -> BuildResult:
        """Build the site. ``progress(i, total, path)`` is called per route during
        the render phase (used by the CLI to show a progress indicator)."""
        # `start` covers the load too, so result.duration is the whole build and the
        # per-phase entries in result.perf (collections/content/setup + render/…)
        # sum to roughly the total.
        start = time.monotonic()
        self._do_load()  # reflect current on-disk content/templates (runs before_load/on_setup)
        self.plugins.run_hook("before_build", self)
        # Drafts/scheduled are hidden for production builds (default), but shown
        # in non-production envs (development, preview, etc.).
        self._production = self.env_name in (None, "production")
        out_dir = self.config.dir_output()
        self.graph.prepare(clean=clean)
        if clean and out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        routes = self.resolve_routes()
        result = BuildResult(
            collections=len(self.store.names()),
            entries=sum(len(self.store.get_collection(n)) for n in self.store.names()),
        )
        # Load-phase timings (collections/content/setup, collected in `_do_load`),
        # reported alongside the render/asset/output phases below.
        result.perf.update(self._perf)
        valid: set[str] = set()
        rendered_pages: dict[str, str] = {}
        _t = time.monotonic()
        total_routes = len(routes)
        for _i, route in enumerate(routes, 1):
            if progress is not None:
                progress(_i, total_routes, route.path)
            _log_render.debug(f"render {route.path}")
            valid.add(route.path)
            out_rel = output_path_for(route.path)
            is_html = route.content_type == "text/html"
            is_page = is_html and not out_rel.endswith((".txt", ".json", ".xml"))
            cache_key = route.cache_key

            # 1) Reuse a cached output when data + content deps are unchanged.
            #    A registered html transform may depend on plugin code, so once any
            #    exists we re-render every route (content-body caching still works).
            #    A source transform rewrites the template itself, so it gets the
            #    same treatment.
            if (
                not self._html_transforms
                and not self._source_transforms
                and self.graph.can_skip(route.path, cache_key, out_rel)
            ):
                dst = out_dir / out_rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(self.graph.reuse_output(route.path, out_rel))
                result.skipped += 1
                (result.pages if is_page else result.endpoints).append(route.path)
                continue

            # 2) Render, record content deps, write to dist + cache.
            rendered = self.render_route(route)
            if rendered is None:
                continue
            content, content_type = rendered
            if content_type == "text/html":
                rendered_pages[route.path] = content
            # Combined scoped CSS + JS are written once for the whole site and
            # injected into every page after the loop (see _write_combined_bundles).
            # optional HTML minification (skips <pre>/<script>/<style>)
            if content_type == "text/html" and self.config.build.compress_html:
                from .minify import minify_html

                content = minify_html(content)
            dst = out_dir / out_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(content, encoding="utf-8")
            self.graph.record_rendered(route.path, cache_key, out_rel, content)
            (result.pages if is_page else result.endpoints).append(route.path)

        self.graph.finish(valid)
        result.perf["render"] = time.monotonic() - _t

        # assets + static passthrough
        self.plugins.run_hook("on_assets", self)
        _t = time.monotonic()
        self.assets.build(out_dir)
        result.perf["assets"] = time.monotonic() - _t
        _t = time.monotonic()
        self.images.build(out_dir)
        self.session.write_combined_bundles(out_dir, self.config.cache_dir())
        result.perf["images_bundles"] = time.monotonic() - _t
        result.asset_warnings = list(self.assets.warnings) + list(self.session.warnings)

        # generated outputs: sitemap, robots, 404, search index
        _t = time.monotonic()
        outputs.write_sitemap(self, out_dir, routes)
        outputs.write_robots(self, out_dir)
        outputs.write_llms(self, out_dir, routes)
        outputs.write_rss(self, out_dir, routes)
        outputs.write_404(self, out_dir, routes)
        outputs.write_search_index(self, out_dir, routes, rendered_pages)
        result.perf["outputs"] = time.monotonic() - _t

        # Project-Pages support: prefix root-relative URLs with [build] base.
        self._apply_base_prefix(out_dir)

        result.duration = time.monotonic() - start
        self.plugins.run_hook("after_build", self, result)
        self._production = False
        return result

    # -- dev server ---------------------------------------------------------
    def render_at(self, path: str) -> tuple[str, str] | None:
        """Render a single URL (for the dev server)."""
        routes = self.resolve_routes()
        for r in routes:
            if r.path == path:
                return self.render_route(r)
        return None

    def build_graph(self) -> dict:
        """Render all routes in-memory and return the build graph
        ``{routes: [...], edges: {path: [deps]}}`` — used by ``epresso inspect``."""
        assert self.env is not None, "site not loaded"
        routes = self.resolve_routes()
        for r in routes:
            self.render_route(r)
        edges = {
            path: sorted(self.graph.edges_for(path))
            for path in sorted({r.path for r in routes})
        }
        return {"routes": [r.path for r in routes], "edges": edges}

    def graph_dot(self) -> str:
        """Render the build graph as a Graphviz DOT string."""
        g = self.build_graph()
        lines = ["digraph epresso {", '  rankdir="LR";']
        for path in g["routes"]:
            lines.append(f'  "{path}" [shape=box];')
        for path, deps in g["edges"].items():
            for dep in deps:
                lines.append(f'  "{dep}" -> "{path}";')
        lines.append("}")
        return "\n".join(lines)
