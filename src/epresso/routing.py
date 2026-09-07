"""Routing — routes-as-code.

``pages/`` files become routes:
  * ``pages/about.md``            → direct Markdown page (layout via front matter)
  * ``pages/blog/[slug].html``    → template route; ``[slug].py`` sidecar exports ``get_static_paths()``
  * ``pages/about.html``          → static template route (no sidecar)
  * ``pages/robots.txt.py``       → endpoint exporting ``get(context) -> (content_type, body)``

Route parts: static, ``{param}``, ``{...param}`` (spread). Clean directory URLs
with a configurable trailing slash.
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from .document import parse_document
from .errors import RouteError
from .pipeline import file_digest

__all__ = ["Route", "RoutePattern", "discover_route_patterns", "expand_pattern", "output_path_for", "parse_route", "paginate"]


@dataclass
class Route:
    """A concrete route to render/write."""

    path: str  # URL path, e.g. ``/blog/hello/`` or ``/robots.txt``
    template: str | None = None  # template name for HTML routes
    template_str: str | None = None  # inline template (from a .ep file body)
    params: dict[str, Any] = field(default_factory=dict)
    data: Any = None  # props passed to the template
    content_type: str = "text/html"
    body: str | None = None  # raw body for endpoint routes
    source: Path | None = None
    # Incremental-build key: data identity. If the user (or the sidecar) does not
    # supply one, we derive it from the rendered content entry's digest so that a
    # content change re-renders only that path.
    cache_key: str | None = None
    scoped_css: str = ""  # component-scoped CSS (from .ep <style> blocks)
    scope_hash: str = ""  # deterministic scoping attribute value
    scripts: str = ""  # client JS (from .ep <script> blocks)
    script_hash: str = ""  # deterministic bundle hash
    frontmatter: dict[str, Any] = field(default_factory=dict)  # .ep frontmatter vars
    redirect_to: str | None = None  # if set, this route is a redirect (not a page)
    redirect_status: int = 301  # HTTP status for the redirect


def _route_part_split(segment: str) -> list[dict[str, Any]]:
    """Parse a file-name segment like ``[slug]`` or ``[...slug]`` into parts."""
    parts: list[dict[str, Any]] = []
    rest = segment
    while rest:
        start = rest.find("[")
        if start == -1:
            if rest:
                parts.append({"content": rest, "dynamic": False, "spread": False})
            break
        if start > 0:
            parts.append({"content": rest[:start], "dynamic": False, "spread": False})
        end = rest.find("]", start)
        if end == -1:
            raise RouteError(f"unterminated dynamic segment: {segment!r}")
        content = rest[start + 1 : end]
        spread = content.startswith("...")
        parts.append({"content": content[3:] if spread else content, "dynamic": True, "spread": spread})
        rest = rest[end + 1 :]
    return parts


def parse_route(pattern_path: Path) -> tuple[list[list[dict[str, Any]]], dict[str, Any]]:
    """Parse a relative pages/ path into segments of route parts."""
    segments: list[list[dict[str, Any]]] = []
    names: dict[str, Any] = {}
    parts = pattern_path.parts
    for seg in parts[:-1]:  # directories
        seg_parts = _route_part_split(seg)
        segments.append(seg_parts)
        for p in seg_parts:
            if p["dynamic"] and not p["spread"]:
                names[p["content"]] = None
            elif p["dynamic"] and p["spread"]:
                names[p["content"]] = None
    filename = parts[-1]
    stem = Path(filename).stem  # strip extension
    if stem in {"index"}:
        # index -> directory root segment (empty)
        segments.append([])
    else:
        file_seg_parts = _route_part_split(stem)
        segments.append(file_seg_parts)
        for p in file_seg_parts:
            if p["dynamic"]:
                names[p["content"]] = None
    return segments, names


def _build_path(segments: list[list[dict[str, Any]]], params: dict[str, Any], trailing: str) -> str:
    out = []
    for seg in segments:
        piece = ""
        for p in seg:
            if not p["dynamic"]:
                piece += p["content"]
            elif p["spread"]:
                piece += "/".join(str(x) for x in params.get(p["content"], [])) if isinstance(params.get(p["content"]), list) else str(params.get(p["content"], ""))
            else:
                val = params.get(p["content"])
                if val is None:
                    raise RouteError(f"missing param {p['content']!r}")
                piece += str(val)
        if piece:
            out.append(piece)
    path = "/" + "/".join(out)
    # Skip trailing slash for file-style paths (endpoints, assets) like /robots.txt.
    if trailing == "always" and path != "/" and "." not in path.rsplit("/", 1)[-1]:
        path += "/"
    return path


def output_path_for(route_path: str) -> str:
    """Map a URL path to a relative output file path under dist/."""
    if route_path == "/":
        return "index.html"
    last = route_path.rstrip("/").split("/")[-1]
    if "." in last and not route_path.endswith("/"):
        # file-style URL (endpoint / asset), e.g. /robots.txt
        return route_path.lstrip("/")
    # directory-style clean URL -> index.html (even if the dir name has a dot,
    # e.g. a repo named 996.ICU -> /996icu/996.ICU/)
    return route_path.lstrip("/").rstrip("/") + "/index.html"


def redirect_routes(config: Any) -> list[Route]:
    """Expand the ``redirects`` config map into meta-refresh HTML redirect pages.

    Each ``{from: to}`` pair becomes a Route that renders a tiny HTML page which
    meta-refreshes to the destination. Target may be a string (301) or a
    ``{destination, status}`` dict (301 permanent / 302 temporary).
    """
    from hashlib import sha256

    out: list[Route] = []
    for item in getattr(config, "redirects", []) or []:
        for src, dst in item.items():
            if isinstance(dst, str):
                destination, status = dst, 301
            else:
                destination = str(dst["destination"])
                status = int(dst.get("status", 301))
            path = "/" + src.strip("/") + "/" if src.strip("/") else "/"
            # data-epresso-status reflects the configured HTTP status for edge/host
            # rewrites; the page itself uses a browser-safe meta refresh.
            body = (
                f"<!doctype html><html><head>"
                f"<meta charset='utf-8'><meta data-epresso-status='{status}' http-equiv='refresh' "
                f"content='0; url={destination}'></head>"
                f"<body><a href='{destination}'>moved</a></body></html>"
            )
            out.append(
                Route(
                    path=path,
                    content_type="text/html",
                    body=body,
                    cache_key=sha256(f"{src}->{destination}:{status}".encode()).hexdigest(),
                    redirect_to=destination,
                    redirect_status=status,
                )
            )
    return out


def paginate(entries: list, per_page: int, base_path: str, *, template: str | None = None):
    """Split ``entries`` into page routes: ``base_path/``, ``base_path/page/N/`` …

    Returns a list of ``Route`` objects suitable for a ``get_static_paths()``
    return value. Each route carries ``params={"page": n}`` and
    ``data={"entries": [...], "page": n, "num_pages": N, "prev": ..., "next": ...}``.
    """
    per_page = max(1, int(per_page))
    entries = list(entries)
    total = len(entries)
    num_pages = max(1, -(-total // per_page))
    routes = []
    base = base_path.rstrip("/")
    for n in range(1, num_pages + 1):
        chunk = entries[(n - 1) * per_page : n * per_page]
        path = (base if n == 1 else f"{base}/page/{n}") + "/"
        prev_path = (base + "/") if n == 2 else (f"{base}/page/{n - 1}/") if n > 1 else None
        routes.append(
            Route(
                path=path,
                template=template,
                params={"page": n},
                data={
                    "entries": chunk,
                    "page": n,
                    "num_pages": num_pages,
                    "prev": prev_path,
                    "next": (f"{base}/page/{n + 1}/") if n < num_pages else None,
                },
            )
        )
    return routes


@dataclass
class RoutePattern:
    """A ``pages/`` file before expansion into concrete routes."""

    file: Path  # absolute path
    rel: Path  # relative to pages/
    segments: list[list[dict[str, Any]]]
    params: dict[str, Any]
    kind: str  # 'direct_md' | 'template' | 'endpoint' | 'epresso'
    sidecar: Path | None = None

    @property
    def dynamic(self) -> bool:
        return bool(self.params)


def discover_route_patterns(pages_dir: Path) -> list[RoutePattern]:
    if not pages_dir.exists():
        return []
    patterns: list[RoutePattern] = []
    files = sorted(pages_dir.rglob("*"))
    from .private import is_private

    for f in files:
        if not f.is_file():
            continue
        if is_private(f.relative_to(pages_dir)):
            continue  # skip _-prefixed files/dirs (private, not routes)
        suffix = f.suffix.lower()
        rel = f.relative_to(pages_dir)
        if suffix == ".md":
            segments, params = parse_route(f.relative_to(pages_dir))
            patterns.append(RoutePattern(f, rel, segments, params, "direct_md"))
        elif suffix == ".ep":
            # single-file route: Python frontmatter + Jinja body
            segments, params = parse_route(f.relative_to(pages_dir))
            patterns.append(RoutePattern(f, rel, segments, params, "epresso"))
        elif suffix == ".html":
            segments, params = parse_route(f.relative_to(pages_dir))
            sidecar = f.with_suffix(".py")
            patterns.append(
                RoutePattern(f, rel, segments, params, "template", sidecar if sidecar.exists() else None)
            )
        elif suffix == ".py":
            # endpoint OR a sidecar for an .html (handled there). Only add if no sibling .html.
            sibling_html = f.with_suffix(".html")
            if sibling_html.exists():
                continue
            segments, params = parse_route(f.relative_to(pages_dir))
            patterns.append(RoutePattern(f, rel, segments, params, "endpoint"))
    return patterns


def _load_module(path: Path, globals_extra: dict[str, Any] | None = None) -> Any:
    name = "_epresso_route_" + "_".join(p for p in path.parts if p not in {".", ".."})
    name = (
        name.replace("[", "_").replace("]", "_").replace(".", "_")
        .replace("/", "_").replace("\\", "_").replace("-", "_")
    )
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RouteError(f"cannot load route module: {path}", path=str(path))
    module = importlib.util.module_from_spec(spec)
    if globals_extra:
        module.__dict__.update(globals_extra)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _scope_hash(rel: Path) -> str:
    import hashlib

    return hashlib.sha1(rel.as_posix().encode()).hexdigest()[:8]


def _script_hash(content: str) -> str:
    import hashlib

    return hashlib.sha1(content.encode("utf-8")).hexdigest()[:12] if content.strip() else ""


def _load_epresso_frontmatter(path: Path, data_api: Any) -> Any:
    """Exec the Python frontmatter of a .ep file (site injected), return the module."""
    frontmatter = parse_document(path.read_text(encoding="utf-8"), "ep").frontmatter
    code = compile(frontmatter, str(path), "exec")
    namespace: dict[str, Any] = {"site": data_api}
    try:
        exec(code, namespace)
    except Exception as e:  # noqa: BLE001
        raise RouteError(f"error in {path.name} frontmatter: {e}\n{traceback.format_exc()}", path=str(path)) from e
    return namespace


def _entry_digest(data: Any) -> str | None:
    return getattr(data, "digest", None)


def expand_pattern(pattern: RoutePattern, trailing: str, data_api: Any) -> list[Route]:
    """Expand a RoutePattern into concrete Routes (calling get_static_paths for templates)."""
    if pattern.kind == "direct_md":
        # direct markdown: single route (static). cache_key = file digest so a
        # content edit re-renders only this page.
        return [
            Route(
                path=_build_path(pattern.segments, {}, trailing),
                source=pattern.file,
                cache_key=file_digest(pattern.file),
            )
        ]

    if pattern.kind == "template":
        tmpl_name = pattern.rel.as_posix().replace("\\", "/")
        if pattern.sidecar:
            module = _load_module(pattern.sidecar, {"site": data_api})
            gsp = getattr(module, "get_static_paths", None)
            if not callable(gsp):
                raise RouteError(f"{pattern.sidecar.name} must export get_static_paths()", path=str(pattern.sidecar))
            try:
                raw_routes = gsp()
            except Exception as e:  # noqa: BLE001
                raise RouteError(f"get_static_paths() failed in {pattern.sidecar.name}: {e}\n{traceback.format_exc()}", path=str(pattern.sidecar)) from e
            out: list[Route] = []
            for r in list(raw_routes or []):  # type: ignore[union-attr]
                if isinstance(r, Route):
                    params = r.params
                    path = r.path
                    cache_key = r.cache_key
                    data = r.data
                else:
                    # dict: {path?, params?, data?, cacheKey?}
                    params = dict(r.get("params", {}))
                    path = r.get("path") or _build_path(pattern.segments, params, trailing)
                    cache_key = r.get("cacheKey")
                    data = r.get("data", None)
                # Auto-derive cache_key from a rendered content entry's digest so
                # content edits re-render only the affected paths.
                if cache_key is None:
                    cache_key = _entry_digest(data)
                out.append(
                    Route(
                        path=path,
                        template=tmpl_name,
                        params=params,
                        data=data,
                        source=pattern.file,
                        cache_key=cache_key,
                    )
                )
            return out
        # static template (no sidecar): single route; cache_key = template file
        # digest so data-only edits can still be incremental (contentHashes track
        # the collections the template consumes).
        return [
            Route(
                path=_build_path(pattern.segments, {}, trailing),
                template=tmpl_name,
                source=pattern.file,
                cache_key=file_digest(pattern.file),
            )
        ]

    if pattern.kind == "epresso":
        # single-file route: Python frontmatter + Jinja body
        namespace = _load_epresso_frontmatter(pattern.file, data_api)
        doc = parse_document(pattern.file.read_text(encoding="utf-8"), "ep")
        body, scoped_css, scripts = doc.body, doc.scoped_css, doc.scripts
        scope_hash = _scope_hash(pattern.rel)
        script_hash = _script_hash(scripts)
        frontmatter_vars = {
            k: v for k, v in namespace.items() if not k.startswith("_") and k != "site"
        }
        # .ep endpoint: frontmatter exports get() -> (content_type, body), e.g. rss.xml.ep
        get_fn = namespace.get("get")
        if callable(get_fn):
            content_type, body_out = get_fn()
            path = _build_path(pattern.segments, {}, trailing)
            return [
                Route(path=path, content_type=content_type, body=body_out, source=pattern.file)
            ]
        gsp = namespace.get("get_static_paths")
        # Not an endpoint => body is a Jinja template: enforce components-over-
        # Jinja composition here (endpoints return generated content, skip them).
        from .enforce import ensure_components

        ensure_components(body, label=str(pattern.file))
        out: list[Route] = []
        if callable(gsp):
            try:
                raw_routes = gsp()
            except Exception as e:  # noqa: BLE001
                raise RouteError(f"get_static_paths() failed in {pattern.file.name}: {e}\n{traceback.format_exc()}", path=str(pattern.file)) from e
            for r in list(raw_routes or []):  # type: ignore[union-attr]
                if isinstance(r, Route):
                    params = r.params
                    path = r.path
                    cache_key = r.cache_key
                    data = r.data
                else:
                    params = dict(r.get("params", {}))
                    path = r.get("path") or _build_path(pattern.segments, params, trailing)
                    cache_key = r.get("cacheKey")
                    data = r.get("data", None)
                if cache_key is None:
                    cache_key = _entry_digest(data)
                out.append(Route(path=path, template_str=body, params=params, data=data, source=pattern.file, cache_key=cache_key, scoped_css=scoped_css, scope_hash=scope_hash, scripts=scripts, script_hash=script_hash, frontmatter=frontmatter_vars))
            return out
        # no get_static_paths -> single static route
        return [
            Route(
                path=_build_path(pattern.segments, {}, trailing),
                template_str=body,
                source=pattern.file,
                cache_key=file_digest(pattern.file),
                scoped_css=scoped_css,
                scope_hash=scope_hash,
                scripts=scripts,
                script_hash=script_hash,
                frontmatter=frontmatter_vars,
            )
        ]

    if pattern.kind == "endpoint":
        module = _load_module(pattern.file, {"site": data_api})
        get_fn: Callable[..., tuple[str, str]] = cast(Callable[..., tuple[str, str]], getattr(module, "get", None))
        if not callable(get_fn):
            raise RouteError(f"{pattern.file.name} must export get()", path=str(pattern.file))
        try:
            content_type, body = get_fn()
        except Exception as e:  # noqa: BLE001
            raise RouteError(f"get() failed in {pattern.file.name}: {e}\n{traceback.format_exc()}", path=str(pattern.file)) from e
        path = _build_path(pattern.segments, {}, trailing)
        return [Route(path=path, content_type=content_type, body=body, source=pattern.file)]

    return []
