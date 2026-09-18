"""Development server — Starlette + watchfiles, WebSocket live-reload.

Shares the Site's render path (same engine as production). Injects a small
live-reload client that subscribes to ``/__epresso_reload``.
"""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, PlainTextResponse, Response
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket

from .logger import get_logger
from .site import Site

DEFAULT_PORT = 4321
log = get_logger("server")


def find_free_port(host: str, preferred: int, limit: int = 20) -> int:
    """Return the first free port at or above ``preferred`` (incrementing +1).

    Returns ``preferred`` if it is free, otherwise the next free port up to
    ``preferred + limit``; falls back to ``preferred`` if none are free.
    """
    import socket

    for p in range(preferred, preferred + limit):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, p))
                return p
            except OSError:
                continue
    return preferred


class DevServer:
    def __init__(self, site: Site, host: str = "127.0.0.1", port: int = DEFAULT_PORT) -> None:
        self.site = site
        self.host = host
        self.port = port
        self.clients: set[WebSocket] = set()
        # Dev serves source files un-hashed, so asset() must return un-hashed URLs.
        site.config.assets.hash = False
        self._search_index_generated = False

    def _handle(self, path: str) -> Response:
        if path == "/":
            path = "/"
        # try exact, else directory index
        candidate = path if path.endswith("/") else path + "/"
        # Serve configured redirects as a real HTTP redirect.
        # (The static build still emits a meta-refresh page.)
        for r in self.site.resolve_routes():
            if r.path == candidate and r.redirect_to:
                from starlette.responses import RedirectResponse

                return RedirectResponse(r.redirect_to, status_code=r.redirect_status)
        rendered = self.site.render_at(candidate) or self.site.render_at(path)
        if rendered is None:
            # serve a static file from public/ or assets/ (dev, un-hashed)
            static = self._static_file(path)
            if static is not None:
                return static
            # Generate the search index on demand, but only for its own URL.
            search_path = "/" + self.site.config.search.index.lstrip("/")
            if path == search_path:
                idx = self._dev_search_index()
                if idx is not None and idx.is_file():
                    from starlette.responses import FileResponse

                    return FileResponse(idx)
            not_found = self.site.render_at("/404/") or self.site.render_at("/404.html")
            if not_found:
                html = self.site.session.inject_page_bundles(
                    not_found[0], self.site.config.dir_output(), self.site.config.cache_dir()
                )
                return HTMLResponse(_inject_reload(html), status_code=404)
            return PlainTextResponse("404 not found", status_code=404)
        self._build_images()  # build any image jobs registered during render (WebP)
        html, content_type = rendered
        if content_type == "text/html":
            # Inject the current render's component-scoped CSS links + page scripts
            # (from .ep <style>/<script> blocks). The build() path does this too;
            # dev must, or scoped styles / interactive scripts are missing.
            html = self.site.session.inject_page_bundles(
                html, self.site.config.dir_output(), self.site.config.cache_dir()
            )
            from . import devtoolbar

            html = devtoolbar.inject(html, self.site, candidate)
            html = _inject_reload(html)
        # Dev renders on every request, so a cached copy is always the wrong one:
        # without this a browser can keep showing a page from before an edit (or
        # from a moment when a template was half-written) long after a reload.
        return HTMLResponse(html, media_type=content_type, headers={"Cache-Control": "no-store"})

    def _dev_search_index(self):
        """Lazily build + cache the search index for the dev server."""
        cfg = self.site.config.search
        if not cfg.enabled:
            return None
        out = self.site.config.dir_output() / cfg.index
        if self._search_index_generated:
            return out if out.is_file() else None
        self._search_index_generated = True
        from . import outputs

        routes = list(self.site.resolve_routes())
        rendered: dict[str, str] = {}
        for r in routes:
            if not outputs._is_html_page(r.path):
                continue
            page = self.site.render_at(r.path)
            if page:
                rendered[r.path] = page[0]
        outputs.write_search_index(self.site, self.site.config.dir_output(), routes, rendered)
        return out if out.is_file() else None

    def _build_images(self) -> None:
        """Build image jobs registered during render (SVG→WebP etc.) into dist/."""
        if getattr(self.site.images, "_jobs", None):
            self.site.images.build(self.site.config.dir_output())

    def _static_file(self, path: str) -> Response | None:
        from starlette.responses import FileResponse, PlainTextResponse, Response

        rel = path.lstrip("/")
        # Scoped CSS and page scripts are build-time outputs; serve the last
        # build's copies so <style>/<script> in .ep work in dev too.
        if rel.startswith(("_scoped/", "_epresso/")):
            art = (self.site.config.dir_output() / rel).resolve()
            if art.is_file() and self.site.config.dir_output().resolve() in art.parents:
                # Unversioned dev bundles are rewritten in place on CSS edits; tell
                # the browser to revalidate so live reload picks up changes.
                #
                # Read the bytes here instead of handing Starlette a FileResponse:
                # a concurrent `epresso build` wipes dist/, and FileResponse opens
                # the file while streaming — a delete between the check above and
                # the read escaped as FileNotFoundError, i.e. a 500 for the
                # <script> request and with it every page's JS.
                try:
                    body = art.read_bytes()
                except OSError:
                    body = None
                if body is not None:
                    media = "text/css" if art.suffix == ".css" else "text/javascript"
                    return Response(body, media_type=media, headers={"Cache-Control": "no-cache"})
            # Never fall through to the HTML 404 page for a build artifact: a
            # `<script src>` answered with an HTML body is a syntax error in the
            # browser, which hides the real cause (a missing file) behind a dead
            # module. Answer with a plain 404 instead.
            return PlainTextResponse("not found", status_code=404)
        # Generated images (WebP from the image pipeline) live under dist/images/
        if rel.startswith("images/"):
            img = (self.site.config.dir_output() / rel).resolve()
            if img.is_file() and self.site.config.dir_output().resolve() in img.parents:
                return FileResponse(img)
        # public/ files live at the URL root (/favicon.ico → public/favicon.ico)
        pub_root = self.site.config.dir_static().resolve()
        pub = (pub_root / rel).resolve()
        if pub == pub_root or pub_root in pub.parents:
            if pub.is_file():
                return FileResponse(pub)
            # directory index (e.g. a static subsite at public/docs/ served at /docs/)
            idx = pub / "index.html"
            if pub.is_dir() and idx.is_file():
                return FileResponse(idx)
        # top-level assets/ files (favicon.svg, robots.txt) are copied to the output
        # root at build time; serve them at the root URL in dev too.
        assets_root = self.site.config.dir_assets()
        top = (assets_root / rel).resolve()
        if (
            top.is_file()
            and assets_root.resolve() in top.parents
            and top.parent == assets_root.resolve()
        ):
            return FileResponse(top)
        # assets/ + styles/ files are served under /assets/<file> (strip the prefix)
        rel2 = rel[len("assets/") :] if rel.startswith("assets/") else rel
        for base in (assets_root, self.site.config.dir_styles()):
            ass = (base / rel2).resolve()
            if ass.is_file() and base.resolve() in ass.parents:
                # CSS entry points (e.g. tailwind.css with @import) must be processed
                # in dev too, otherwise utilities don't apply.
                if ass.suffix.lower() == ".css" and rel2 in self.site.config.assets.css:
                    processed = self._process_css_for_dev(ass)
                    if processed is not None:
                        # Dev re-processes this on every request, and the result changes
                        # with the source — but nothing here is a validator, so without
                        # this a browser can keep serving a stylesheet from before an
                        # edit (a CSS fix then looks like it "did not work").
                        return Response(
                            content=processed,
                            media_type="text/css",
                            headers={"Cache-Control": "no-cache"},
                        )
                return FileResponse(ass)
        # Fall back to the bundled default favicon so /favicon.ico never 404s.
        if rel == "favicon.ico":
            default = Path(__file__).resolve().parent / "static" / "favicon.ico"
            if default.is_file():
                return FileResponse(default)
        return None

    def _process_css_for_dev(self, src: Path) -> str | None:
        from .css import CSSProcessor

        proc = CSSProcessor(self.site.config)
        out = self.site.config.root / ".ep" / "dev-css" / src.name
        out.parent.mkdir(parents=True, exist_ok=True)
        result = proc.process(src, out.parent)
        if result is not None and result.exists():
            return result.read_text(encoding="utf-8")
        # fallback: raw source
        return src.read_text(encoding="utf-8")

    async def _route(self, request: Request) -> Response:
        return self._handle(request.url.path)

    async def _ws(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.add(ws)
        try:
            while True:
                await ws.receive_text()  # keepalive
        except Exception:  # noqa: BLE001
            pass
        finally:
            self.clients.discard(ws)

    async def broadcast_reload(self) -> None:
        for ws in list(self.clients):
            try:
                await ws.send_text("reload")
            except Exception:  # noqa: BLE001
                self.clients.discard(ws)

    async def _broadcast(self, text: str) -> None:
        for ws in list(self.clients):
            try:
                await ws.send_text(text)
            except Exception:  # noqa: BLE001
                self.clients.discard(ws)

    def build_app(self) -> Starlette:
        return Starlette(
            routes=[
                Route("/{path:path}", self._route),
                WebSocketRoute("/__epresso_reload", self._ws),
            ]
        )

    def run(self) -> None:
        app = self.build_app()
        watch_root = self.site.config.root

        # Directories whose changes must never trigger a reload: vendored/
        # generated output (dist is written as dev serves scoped css, .cache holds
        # the incremental + fetched-layer cache), git/VCS, dependencies and the
        # local scratch dir. watchfiles has no ignore_dirs kwarg, so filter events
        # by path here.
        _IGNORED_DIRS = {"node_modules", ".git", ".venv", "dist", "__pycache__", ".ep", ".cache"}

        async def watcher():
            # watchfiles.watch() is a *blocking* generator. Push its batches into a
            # queue from a helper thread and do the reload work on this (uvicorn)
            # event loop so it stays serialized with requests.
            from watchfiles import watch

            # Local layer dirs live outside the project root by design; watch them
            # too so editing a vendored/adjacent components dir reloads the page.
            watch_paths = [str(watch_root)]
            for layer in getattr(self.site, "layers", []):
                inside = layer.root == watch_root or watch_root in layer.root.parents
                if layer.kind == "path" and not inside:
                    watch_paths.append(str(layer.root))

            events_q: asyncio.Queue = asyncio.Queue()

            def _produce() -> None:
                try:
                    for changes in watch(*watch_paths):
                        events_q.put_nowait(changes)
                except Exception as e:  # noqa: BLE001
                    log.error(f"file watcher stopped: {e}")

            threading.Thread(target=_produce, daemon=True, name="epresso-file-watch").start()
            while True:
                changes = await events_q.get()
                relevant = any(
                    not any(seg in _IGNORED_DIRS for seg in Path(path).parts)
                    for _change, path in changes
                )
                if not relevant:
                    continue
                try:
                    self.site._do_load()  # reload content/collections so edits are picked up
                    self.site.plugins.run_hook("before_build", self.site)
                except Exception as e:  # noqa: BLE001
                    log.error(f"reload failed: {e}")
                    await self._broadcast("error: reload failed — " + str(e)[:300])
                    continue
                await self.broadcast_reload()

        # Run uvicorn and the file-watcher on the SAME event loop. Scheduling the
        # watcher on its own loop and calling uvicorn.run() (which starts a second
        # loop) would mean the watcher never runs, so live reload never fires.
        from uvicorn import Config, Server

        config = Config(app, host=self.host, port=self.port, log_level="warning")
        server = Server(config)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(watcher())
        log.info(f"epresso dev → http://{self.host}:{self.port}")
        try:
            loop.run_until_complete(server.serve())
        finally:
            for task in asyncio.all_tasks(loop):
                task.cancel()
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()


def _build_static_app(dist: Path, site=None):
    """Starlette app serving a built ``dist/`` statically, with the generated
    ``404.html`` (if any) served for unknown paths.

    When ``site`` is given, served HTML pages are rewritten at serve time to
    inject the dev toolbar (live-reload disabled) so private/draft pages show
    their status notification during ``epresso preview``. The files on disk in
    ``dist/`` are never modified.
    """
    from starlette.applications import Starlette
    from starlette.responses import FileResponse, PlainTextResponse
    from starlette.routing import Route

    dist = dist.resolve()

    def file_at(path: str) -> FileResponse | PlainTextResponse | None:
        rel = (dist / path.lstrip("/")).resolve()
        if rel.is_dir():
            rel = rel / "index.html"
        if rel.is_file() and dist in rel.parents:
            return FileResponse(rel)
        return None

    def not_found():
        # Serve the site's generated 404 page (with its layout) if one was built.
        nf = dist / "404.html"
        if nf.is_file():
            return FileResponse(nf, status_code=404)
        return PlainTextResponse("404 not found", status_code=404)

    async def route(request):
        resp = file_at(request.url.path)
        if resp is None:
            return not_found()
        # Serve-time toolbar injection (live-reload disabled) for HTML pages,
        # so private/draft pages show their status notification in preview.
        # The on-disk files in dist/ are never modified.
        if site is not None and site.config.dev.toolbar.enabled:
            rel = (dist / request.url.path.lstrip("/")).resolve()
            if rel.is_dir():
                rel = rel / "index.html"
            if rel.is_file() and rel.suffix.lower() == ".html":
                from . import devtoolbar

                html = rel.read_text(encoding="utf-8", errors="replace")
                out = devtoolbar.inject(html, site, request.url.path, live=False)
                if out is not html:
                    from starlette.responses import HTMLResponse

                    return HTMLResponse(out)
        return resp

    return Starlette(routes=[Route("/{path:path}", route)])


def serve_dist(dist: Path, host: str = "127.0.0.1", port: int = DEFAULT_PORT, site=None) -> None:
    """Serve a built dist/ directory statically."""

    log.info(f"epresso serve → http://{host}:{port}")
    uvicorn.run(_build_static_app(dist, site=site), host=host, port=port)


def _inject_reload(html: str) -> str:
    script = (
        "<script>"
        "(function(){"
        "var ws=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/__epresso_reload');"
        "ws.onmessage=function(){location.reload();};"
        "setTimeout(function(){if(ws.readyState>1){location.reload();}},1500);"
        "})();</script>"
    )
    return html.replace("</body>", script + "</body>") if "</body>" in html else html + script
