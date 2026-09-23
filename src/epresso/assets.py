"""Asset pipeline — content-hashed references, static passthrough, esbuild bundling.

* ``asset(\"css/main.css\")`` → content-hashed copy to ``dist/assets/...``.
* ``public/`` files are copied verbatim to the output root.
* Declared JS/CSS entry points are bundled with esbuild (external binary; falls
  back to a raw copy when esbuild is unavailable so JS stays optional).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from .css import CSSProcessor
from .pipeline import bundle_js, file_digest


class AssetPipeline:
    def __init__(self, config: Any) -> None:
        self.config = config
        self._assets: dict[str, Path] = {}  # hashed URL -> source file
        self._bundled: list[Path] = []  # esbuild output files
        self._warnings: list[str] = []

    # -- reference resolution ------------------------------------------------
    def resolve(self, name: str) -> str:
        """Return the (hashed) public URL for an asset under ``assets/`` or ``styles/``."""
        rel = name.lstrip("/")
        src = self.config.dir_assets() / rel
        if not src.is_file():
            src = self.config.dir_styles() / rel
        if not src.is_file():
            return "/assets/" + rel
        if not self.config.assets.hash:
            return "/assets/" + rel
        base, ext = os.path.splitext(rel)
        digest = file_digest(src, 12)
        url = f"/assets/{base}.{digest}{ext}"
        self._assets[url] = src
        return url

    # -- build ---------------------------------------------------------------
    def build(self, out_dir: Path) -> None:
        self._copy_static(out_dir)
        self._copy_root_assets(out_dir)
        self._copy_default_favicon(out_dir)
        self._copy_hashed_assets(out_dir)
        self._bundle(out_dir)

    def _copy_default_favicon(self, out_dir: Path) -> None:
        """Copy a bundled default favicon.ico to the output root when the site
        ships none (no ``public/favicon.ico`` or top-level ``assets/favicon.ico``),
        so the output always has a ``/favicon.ico``."""
        if (out_dir / "favicon.ico").exists():
            return
        default = Path(__file__).resolve().parent / "static" / "favicon.ico"
        if default.is_file():
            shutil.copyfile(default, out_dir / "favicon.ico")

    def _copy_root_assets(self, out_dir: Path) -> None:
        """Copy top-level files directly in ``assets/`` (e.g. robots.txt, favicon.svg)
        verbatim to the output root, so they land at ``/robots.txt`` / ``/favicon.svg``.
        Files in subdirectories (images/, css/, …) are buildable/referenced assets.
        """
        assets = self.config.dir_assets()
        if not assets.exists():
            return
        from .private import is_private

        for f in assets.iterdir():
            if f.is_file() and not is_private(f):
                shutil.copyfile(f, out_dir / f.name)

    def _copy_static(self, out_dir: Path) -> None:
        from .private import is_private

        static = self.config.dir_static()
        if not static.exists():
            return
        for f in static.rglob("*"):
            if not f.is_file():
                continue
            if is_private(f.relative_to(static)):
                continue  # skip _-prefixed files/dirs
            rel = f.relative_to(static)
            dst = out_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, dst)

    def _copy_hashed_assets(self, out_dir: Path) -> None:
        from .minify import minify_css

        for url, src in self._assets.items():
            dst = out_dir / url.lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            if url.endswith(".css"):
                dst.write_text(minify_css(src.read_text(encoding="utf-8")), encoding="utf-8")
            else:
                shutil.copyfile(src, dst)

    def _bundle(self, out_dir: Path) -> None:
        js = [e for e in self.config.assets.js if e]
        css = [e for e in self.config.assets.css if e]
        if css:
            self._process_css(css, out_dir)
        if js:
            self._bundle_js(js, out_dir)

    def _process_css(self, entries: list[str], out_dir: Path) -> None:
        """Run the CSS processor (PostCSS/Tailwind) on entry points, else copy verbatim."""
        from .minify import minify_css

        processor = CSSProcessor(self.config)
        for entry in entries:
            src = self.config.dir_assets() / entry
            if not src.is_file():
                src = self.config.dir_styles() / entry
            if not src.is_file():
                continue
            out = processor.process(src, out_dir)
            if out is not None:
                # The postcss path runs the project's plugins, which do not minify;
                # tailwind's CLI is already invoked with --minify. (A stylesheet
                # epresso copies verbatim below is left as the author wrote it.)
                if not processor.minifies:
                    out.write_text(minify_css(out.read_text(encoding="utf-8")), encoding="utf-8")
                continue
            # fallback: verbatim copy (CSS stays optional / unprocessed)
            dst = out_dir / "assets" / entry
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
        self._warnings.extend(processor.warnings)

    def _bundle_js(self, entries: list[str], out_dir: Path) -> None:
        sources = [str(self.config.dir_assets() / e) for e in entries]
        result, detail = bundle_js(
            sources,
            outdir=out_dir / "assets",
            entry_names="[name].[hash]",
            minify=True,
        )
        if result == "ok":
            return
        if result == "missing":
            # JS optional: raw-copy the entry files so a pure-Python site still works.
            self._warnings.append("esbuild not found; copying JS entry points verbatim")
            for entry in entries:
                src = self.config.dir_assets() / entry
                if src.is_file():
                    dst = out_dir / "assets" / entry
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dst)
        else:  # failed
            self._warnings.append(f"esbuild failed: {detail}")

    @property
    def warnings(self) -> list[str]:
        return self._warnings
