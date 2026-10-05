"""Bundled epresso plugin: responsive, lazy-loaded content images.

Enable it from ``site.toml`` (the docs theme does)::

    plugins = ["epresso_optimize"]

    [plugin.epresso_optimize]
    widths = [400, 800, 1200]   # WebP variants (never wider than the source)
    sizes = "100vw"             # the <img sizes> hint
    quality = 80
    dev = false                 # also optimise in dev / non-production builds

After a production build every local PNG/JPEG ``<img>`` in the output that isn't
already responsive (no ``srcset`` / ``loading`` / ``width``) gets WebP variants in
``dist/images/``, a ``srcset`` + ``sizes``, ``loading="lazy" decoding="async"`` and
its intrinsic ``width``/``height``. The original file stays as the fallback
``src``. GIF, SVG, external and ``data:`` images are left alone. Needs Pillow
(``pip install 'epresso[images]'``); without it the plugin warns once and
changes nothing. Encoded variants are cached in ``.cache/optimize/``.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from epresso.plugins import Plugin

DEFAULT_WIDTHS = [400, 800, 1200]
_IMG = re.compile(r"<img\b[^>]*>", re.I)
_SRC = re.compile(r'\ssrc="([^"]+)"', re.I)
_SKIP_ATTRS = re.compile(r"\s(?:srcset|loading|width)=", re.I)
EXTS = {".png", ".jpg", ".jpeg"}


def _has_pillow() -> bool:
    try:
        import PIL  # noqa: F401, PLC0415

        return True
    except ImportError:
        return False


class _Optimizer:
    def __init__(self, out: Path, cache: Path, opts: dict[str, Any], base: str) -> None:
        self.out = out
        self.cache = cache
        self.widths = sorted({int(w) for w in opts.get("widths") or DEFAULT_WIDTHS})
        self.sizes = str(opts.get("sizes") or "100vw")
        self.quality = int(opts.get("quality") or 80)
        self.base = "/" + base.strip("/") + "/" if base.strip("/") else "/"
        self.done: dict[Path, tuple[int, int, list[tuple[str, int]]] | None] = {}
        self.images = 0

    def _file(self, src: str, page: Path) -> Path | None:
        u = urlsplit(src)
        if u.scheme or u.netloc or not u.path:
            return None
        path = unquote(u.path)
        if path.startswith("/"):
            if self.base != "/" and path.startswith(self.base):
                path = "/" + path[len(self.base) :]
            f = self.out / path.lstrip("/")
        else:
            f = page.parent / path
        f = f.resolve()
        if f.suffix.lower() not in EXTS or not f.is_file() or not f.is_relative_to(self.out.resolve()):
            return None
        return f

    def _variants(self, f: Path) -> tuple[int, int, list[tuple[str, int]]] | None:
        if f not in self.done:
            self.done[f] = self._compute(f)
            if self.done[f]:
                self.images += 1
        return self.done[f]

    def _compute(self, f: Path) -> tuple[int, int, list[tuple[str, int]]] | None:
        from PIL import Image  # noqa: PLC0415

        try:
            im = Image.open(f)
            w, h = im.size
        except OSError:
            return None
        digest = hashlib.sha256(f.read_bytes()).hexdigest()[:10]
        widths = [x for x in self.widths if x < w] + ([w] if w <= self.widths[-1] else [])
        widths = sorted(set(widths)) or [w]
        urls = []
        for width in widths:
            name = f"{f.stem}-{digest}-{width}.webp"
            dst = self.out / "images" / name
            cached = self.cache / f"{digest}-{width}-q{self.quality}.webp"
            if not cached.is_file():
                img = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
                if width != w:
                    img = img.resize((width, max(1, round(h * width / w))), Image.Resampling.LANCZOS)
                cached.parent.mkdir(parents=True, exist_ok=True)
                img.save(cached, "WEBP", quality=self.quality, method=4)  # 6 is ~7x slower for ~2% smaller
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(cached.read_bytes())
            urls.append((self.base + "images/" + name, width))
        return (w, h, urls)

    def rewrite(self, html: str, page: Path) -> str:
        def repl(m: re.Match[str]) -> str:
            tag = m.group(0)
            sm = _SRC.search(tag)
            if not sm or _SKIP_ATTRS.search(tag):
                return tag
            f = self._file(sm.group(1), page)
            v = f and self._variants(f)
            if not v:
                return tag
            w, h, urls = v
            srcset = ", ".join(f"{u} {width}w" for u, width in urls)
            extra = f' srcset="{srcset}" sizes="{self.sizes}" width="{w}" height="{h}" loading="lazy" decoding="async"'
            end = -2 if tag.endswith("/>") else -1
            return tag[:end].rstrip() + extra + tag[end:]

        return _IMG.sub(repl, html) if "<img" in html else html

    def _encode_all(self, pages: list[Path]) -> None:
        """Encode every referenced image up front, in parallel (Pillow releases
        the GIL while encoding), so the page rewrite below only hits the cache."""
        from concurrent.futures import ThreadPoolExecutor  # noqa: PLC0415

        files: dict[Path, None] = {}
        for page in pages:
            html = page.read_text(encoding="utf-8")
            for tag in _IMG.findall(html):
                sm = _SRC.search(tag)
                f = sm and not _SKIP_ATTRS.search(tag) and self._file(sm.group(1), page)
                if f:
                    files[f] = None
        with ThreadPoolExecutor() as pool:
            results = dict(zip(files, pool.map(self._compute, files), strict=True))
        for f, v in results.items():
            self.done[f] = v
            if v:
                self.images += 1

    def run(self) -> tuple[int, int]:
        pages = 0
        html_pages = list(self.out.rglob("*.html"))
        self._encode_all(html_pages)
        for page in html_pages:
            html = page.read_text(encoding="utf-8")
            new = self.rewrite(html, page)
            if new != html:
                page.write_text(new, encoding="utf-8")
                pages += 1
        return pages, self.images


def epresso_optimize() -> Plugin:
    """Return the ``Plugin`` that makes content images responsive."""
    warned = [False]

    def after_build(caps, result):
        if not (caps.site._production or caps.options.get("dev")):
            return
        if not _has_pillow():
            if not warned[0]:
                caps.logger.warn("Pillow is not installed — images not optimised (pip install 'epresso[images]')")
                warned[0] = True
            return
        cfg = caps.config
        opt = _Optimizer(cfg.dir_output(), cfg.cache_dir() / "optimize", dict(caps.options), cfg.build.base or "")
        pages, images = opt.run()
        if images:
            caps.logger.info(f"optimised {images} images on {pages} pages")

    return Plugin(name="epresso_optimize", hooks={"after_build": after_build})


# Module-level instance so ``plugins = ["epresso_optimize"]`` auto-discovers it.
optimize = epresso_optimize()
