"""RenderSession — the side-band output a render produces.

When a route or component renders, it can emit two kinds of *side-band* output
beyond the HTML body: **scoped CSS** (a ``<style>`` block scoped to a component's
``data-epresso-*`` attribute) and **client scripts** (a ``<script>`` block bundled
page-level). This module owns both — where they accumulate, what is *active* in
the current render, and how they are written to ``dist/``.

One ``RenderSession`` lives per build and per dev-server. A render begins with
:meth:`begin_render`, which resets the *active* sets; the *accumulated* maps
persist across renders so a build can emit one combined bundle at the end. The
build and the dev server both ask the session to write its outputs, so there is a
single writer path instead of two.

Callers (components, route rendering) only see the small add/dedup interface;
they never touch ``Site`` internals.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

from .minify import minify_css
from .pipeline import bundle_js

__all__ = ["RenderSession"]

Warn = Callable[[str], None]


def _scope_css(css: str, scope_hash: str) -> str:
    """Scope CSS rules by inserting ``data-epresso-<hash>`` into each selector.

    Deferred import to keep the module-load graph small (the scoping transform
    lives in :mod:`epresso.scoped`).
    """
    from .scoped import scope_css

    return scope_css(css, scope_hash)


class RenderSession:
    """Accumulate + emit the scoped CSS and client scripts a render produces.

    Two lifetimes, deliberately distinct:

    * **Build-lifetime** — ``scoped_css`` and ``scripts`` maps accumulate across
      every render in a build (or dev session), so a build can emit one combined
      bundle. ``scripts_written`` tracks which script files already exist on disk
      (dev path).
    * **Render-lifetime** — ``begin_render`` clears the *active* sets and the
      global-CSS dedup set, so the dev server can ask what *this* render emitted.
    """

    def __init__(self) -> None:
        # build-lifetime accumulation
        self.scoped_css: dict[str, str] = {}  # scope_hash -> rewritten css
        self.scripts: dict[str, str] = {}  # script_hash -> js content
        self._scripts_written: set[str] = set()  # scripts whose files exist on disk
        self.warnings: list[str] = []
        # render-lifetime
        self._scoped_active: set[str] = set()  # scopes used in the current render
        self._scripts_active: set[str] = set()  # scripts used in the current render
        self._global_css_hashes: set[str] = set()  # inline <style> contents already emitted

    # -- render boundary ----------------------------------------------------
    def begin_render(self) -> None:
        """Start a fresh render: clear the per-render active/dedup state."""
        self._scoped_active = set()
        self._scripts_active = set()
        self._global_css_hashes = set()

    # -- accumulation -------------------------------------------------------
    def add_scoped_css(self, scope: str, raw_css: str) -> None:
        """Register a component/route's scoped CSS for ``scope`` and mark it active.

        The rewrite (scoping each selector) happens here, once, so every caller
        passes raw CSS and the session owns the transformation.
        """
        # Scope hashes are path-based (stable across a component's CSS edits), so
        # a component can change its <style> without a new scope id. The dev
        # server's session outlives edits, so refresh the cached rewrite when the
        # raw CSS changed (builds stay deterministic: unchanged components
        # rewrite identically and last-value-wins is a no-op).
        new = _scope_css(raw_css, scope)
        if self.scoped_css.get(scope) != new:
            self.scoped_css[scope] = new
        self._scoped_active.add(scope)

    def dedup_global_css(self, rendered: str) -> str | None:
        """Return a minified inline ``<style>`` for ``rendered`` global CSS, or None.

        Global (``is:global``) styles are emitted inline inside
        each component's HTML; without dedup a component rendered N times on one
        page would inline its whole stylesheet N times. Returns the style HTML
        only the first time per render, else None.
        """
        key = hashlib.sha1(("css:" + rendered).encode()).hexdigest()[:16]
        if key in self._global_css_hashes:
            return None
        self._global_css_hashes.add(key)
        return f"<style>{minify_css(rendered)}</style>"

    def add_script(self, js: str) -> str:
        """Register a client script (dedup by content hash); returns its hash."""
        if not js.strip():
            return ""
        h = hashlib.sha1(js.encode("utf-8")).hexdigest()[:12]
        self.scripts.setdefault(h, js)
        self._scripts_active.add(h)
        return h

    @property
    def active_scopes(self) -> set[str]:
        return set(self._scoped_active)

    @property
    def active_scripts(self) -> set[str]:
        return set(self._scripts_active)

    # -- build path: one combined bundle + inject into every page ------------
    def write_combined_bundles(self, out_dir: Path, cache_dir: Path, warn: Warn | None = None) -> None:
        """Write the site-wide combined scoped-CSS + JS bundles and inject them
        into every built HTML page (one ``<link>`` + one ``<script>`` instead of
        one per component). Scoped selectors don't collide, so concatenation is
        safe."""
        warn = warn or self.warnings.append

        css_url = ""
        if self.scoped_css:
            combined = minify_css(
                "\n".join(self.scoped_css[k] for k in sorted(self.scoped_css))
            )
            h = hashlib.sha1(combined.encode("utf-8")).hexdigest()[:12]
            out = out_dir / "_scoped" / f"epresso.{h}.css"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(combined, encoding="utf-8")
            css_url = f"/_scoped/epresso.{h}.css"

        js_url = ""
        if self.scripts:
            combined = "\n;\n".join(self.scripts[h] for h in sorted(self.scripts))
            h = hashlib.sha1(combined.encode("utf-8")).hexdigest()[:12]
            src = cache_dir / "scripts" / f"epresso.{h}.js"
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text(combined, encoding="utf-8")
            out = out_dir / "_epresso" / f"epresso.{h}.js"
            out.parent.mkdir(parents=True, exist_ok=True)
            result, detail = bundle_js([str(src)], outfile=out)
            if result != "ok":
                if result == "failed":
                    warn(f"combined script esbuild failed: {detail}; writing raw")
                out.write_text(combined, encoding="utf-8")
            js_url = f"/_epresso/epresso.{h}.js"

        self._inject_combined_bundles(out_dir, css_url, js_url)

    def _inject_combined_bundles(self, out_dir: Path, css_url: str, js_url: str) -> None:
        """Insert the combined ``<link>/<script>`` tags into every built HTML file."""
        if not (css_url or js_url):
            return
        for f in out_dir.rglob("*.html"):
            s = f.read_text(encoding="utf-8")
            original = s
            if css_url and css_url not in s:
                if "</head>" in s:
                    s = s.replace("</head>", f'<link rel="stylesheet" href="{css_url}"></head>', 1)
                else:
                    s = f'<link rel="stylesheet" href="{css_url}">' + s
            if js_url and js_url not in s:
                if "</body>" in s:
                    s = s.replace("</body>", f'<script type="module" src="{js_url}"></script></body>', 1)
                else:
                    s = s + f'<script type="module" src="{js_url}"></script>'
            if s != original:
                f.write_text(s, encoding="utf-8")

    # -- dev path: per-page, uses the current render's active sets -----------
    def inject_page_bundles(self, html: str, out_dir: Path, cache_dir: Path) -> str:
        """Write the current render's scoped-CSS + script files and return ``html``
        with the per-page ``<link>/<script>`` tags injected (used by the dev
        server, which serves one page at a time)."""
        if self._scoped_active:
            links = ""
            for scope in sorted(self._scoped_active):
                # Dev serves one page at a time via an *unversioned* per-scope
                # file (epresso-{scope}.css), and the scope id is path-stable, so
                # always rewrite it from the current render's CSS. Otherwise a CSS
                # edit that keeps the same scope id would keep serving the stale
                # file. The build path uses a combined, content-hashed bundle and
                # is unaffected.
                self.write_scoped_css_file(out_dir, scope)
                links += f'<link rel="stylesheet" href="/_scoped/epresso-{scope}.css">'
            html = html.replace("</head>", links + "</head>") if "</head>" in html else links + html

        if self._scripts_active:
            self.write_page_scripts(out_dir, cache_dir)
            tags = "".join(
                f'<script type="module" src="/_epresso/scripts/{h}.js"></script>'
                for h in sorted(self._scripts_active)
            )
            html = html.replace("</body>", tags + "</body>") if "</body>" in html else html + tags

        return html

    def write_scoped_css_file(self, out_dir: Path, scope: str) -> None:
        """Write a single scoped component's CSS (dev path, per-page injection)."""
        out = out_dir / "_scoped" / f"epresso-{scope}.css"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(minify_css(self.scoped_css.get(scope, "")), encoding="utf-8")

    def write_page_scripts(self, out_dir: Path, cache_dir: Path, warn: Warn | None = None) -> None:
        """Write all registered client scripts to ``dist/_epresso/scripts/<hash>.js``.

        Bundles with esbuild when available (so ``import``/bare specifiers work);
        otherwise writes the module verbatim (JS stays optional).
        """
        warn = warn or self.warnings.append
        for h in sorted(self.scripts):
            out = out_dir / "_epresso" / "scripts" / f"{h}.js"
            # `scripts_written` means "already on disk". Re-check the file rather than
            # trusting the set: `epresso build` wipes dist/ (site.build(clean=True)) and a
            # dev server serving the same directory would otherwise keep injecting a URL
            # it never rewrites, so every page's JS 404s until the server restarts.
            if h in self._scripts_written and out.is_file():
                continue
            src = cache_dir / "scripts" / f"{h}.js"
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text(self.scripts[h], encoding="utf-8")
            out.parent.mkdir(parents=True, exist_ok=True)
            result, detail = bundle_js([str(src)], outfile=out)
            if result == "ok":
                self._scripts_written.add(h)
                continue
            if result == "failed":
                warn(f"script {h} esbuild failed: {detail}; writing raw")
            # Re-create the directory: a concurrent `epresso build` (which wipes
            # dist/) can remove it after the mkdir above, and the raw write would
            # then raise FileNotFoundError out of the request handler.
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(self.scripts[h], encoding="utf-8")
            self._scripts_written.add(h)
