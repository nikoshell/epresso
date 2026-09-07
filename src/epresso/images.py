"""Image service — responsive images via Pillow (optional, lazy-imported).

``image(\"hero.jpg\", widths=[640, 1280])`` produces resized WebP variants with a
content-hashed srcset. ``picture(...)`` produces a `<picture>` with WebP sources
plus a JPEG fallback. Pillow is imported only when
images are actually used, so a text-only site pays nothing.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .pipeline import file_digest

DEFAULT_WIDTHS = [400, 800, 1200]

# formats we generate: (extension, PIL format, media type)
FORMATS = {"webp": ("webp", "image/webp"), "jpeg": ("jpg", "image/jpeg")}


def _has_pillow() -> bool:
    try:
        import PIL  # noqa: F401  # type: ignore[import-not-found]  # optional `images` extra

        return True
    except Exception:  # noqa: BLE001
        return False


class ImagePipeline:
    def __init__(self, config: Any) -> None:
        self.config = config
        # source rel -> {(width, format)}
        self._jobs: dict[str, set[tuple[int, str]]] = {}

    def resolve_src(self, name: str) -> Path | None:
        """Locate a source image under assets/ (or public/, or content/)."""
        cands = [self.config.dir_assets() / name.lstrip("/")]
        if hasattr(self.config, "dir_static"):
            cands.append(self.config.dir_static() / name.lstrip("/"))
        if hasattr(self.config, "dir_content"):
            cands.append(self.config.dir_content() / name.lstrip("/"))
        for c in cands:
            if c.is_file():
                return c
        return None

    def _rasterize_svg(self, src: Path, tmp: Path, target_w: int = 400) -> Path | None:
        """Rasterize an SVG to a PNG so Pillow can process it.

        Prefers cairosvg (needs the system cairo library); falls back to the
        inkscape / rsvg-convert CLI when it's available.
        """
        import shutil
        import subprocess

        if src.suffix.lower() != ".svg":
            return src
        png = tmp / f"{src.stem}-{target_w}.png"
        png.parent.mkdir(parents=True, exist_ok=True)
        if png.exists():
            return png  # cached rasterization
        # cairosvg
        try:
            import cairosvg  # type: ignore[import-not-found]  # optional: needs system cairo

            cairosvg.svg2png(url=str(src), write_to=str(png), output_width=target_w)
            return png
        except Exception:  # noqa: BLE001
            pass
        # CLI fallback: inkscape / rsvg-convert
        for cmd in (
            ["inkscape", str(src), "-w", str(target_w), "-o", str(png)],
            ["rsvg-convert", str(src), "-w", str(target_w), "-o", str(png)],
        ):
            if shutil.which(cmd[0]):
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    return png
                except Exception as e:  # noqa: BLE001
                    print(f"  [epresso] {cmd[0]} failed on {src.name}: {e}")
                    return None
        return None

    def _register(self, name: str, widths: list[int], formats: list[str]) -> None:
        for w in widths:
            for fmt in formats:
                self._jobs.setdefault(name.lstrip("/"), set()).add((w, fmt))

    def _fallback(self, name: str, alt: str) -> str:
        return f"<img src=\"/assets/{name.lstrip('/')}\" alt=\"{alt}\">"

    def render(self, name: str, widths: list[int] | None = None, alt: str = "") -> str:
        """Return an <img> tag (WebP srcset) for a source image under assets/."""
        src = self.resolve_src(name)
        if src is None or not _has_pillow():
            return self._fallback(name, alt)
        widths = [int(w) for w in (widths or DEFAULT_WIDTHS)]
        self._register(name, widths, ["webp"])
        base, _ext = os.path.splitext(name.lstrip("/"))
        digest = file_digest(src, 10)
        variants = sorted(widths, reverse=True)
        urls = [f"/images/{base}-{digest}-{w}.webp" for w in variants]
        srcset = ", ".join(f"{u} {w}w" for u, w in zip(urls, variants, strict=True))
        return f"<img src=\"{urls[0]}\" srcset=\"{srcset}\" sizes=\"100vw\" alt=\"{alt}\">"

    def render_cls(
        self, name: str, widths: list[int] | None, alt: str, cls: str, style: str = ""
    ) -> str:
        """Like :meth:`render` but with a custom CSS class (and optional inline style)."""
        style_attr = f" style=\"{style}\"" if style else ""
        src = self.resolve_src(name)
        if src is None or not _has_pillow():
            return f"<img class=\"{cls}\"{style_attr} src=\"/assets/{name.lstrip('/')}\" alt=\"{alt}\">"
        widths = [int(w) for w in (widths or DEFAULT_WIDTHS)]
        self._register(name, widths, ["webp"])
        base, _ext = os.path.splitext(name.lstrip("/"))
        digest = file_digest(src, 10)
        variants = sorted(widths, reverse=True)
        urls = [f"/images/{base}-{digest}-{w}.webp" for w in variants]
        srcset = ", ".join(f"{u} {w}w" for u, w in zip(urls, variants, strict=True))
        return f"<img class=\"{cls}\"{style_attr} src=\"{urls[0]}\" srcset=\"{srcset}\" sizes=\"100vw\" alt=\"{alt}\">"

    def picture(self, name: str, widths: list[int] | None = None, alt: str = "") -> str:
        """Return a <picture> with WebP sources + a JPEG fallback."""
        src = self.resolve_src(name)
        if src is None or not _has_pillow():
            return self._fallback(name, alt)
        widths = [int(w) for w in (widths or DEFAULT_WIDTHS)]
        self._register(name, widths, ["webp", "jpeg"])
        base, _ext = os.path.splitext(name.lstrip("/"))
        digest = file_digest(src, 10)
        variants = sorted(widths, reverse=True)

        webp_srcset = ", ".join(
            f"/images/{base}-{digest}-{w}.webp {w}w" for w in variants
        )
        jpeg_srcset = ", ".join(
            f"/images/{base}-{digest}-{w}.jpg {w}w" for w in variants
        )
        jpeg_src = f"/images/{base}-{digest}-{variants[0]}.jpg"
        return (
            f"<picture>"
            f'<source type=\"image/webp\" srcset=\"{webp_srcset}\" sizes=\"100vw\">'
            f'<img src=\"{jpeg_src}\" srcset=\"{jpeg_srcset}\" sizes=\"100vw\" alt=\"{alt}\">'
            f"</picture>"
        )

    def build(self, out_dir: Path) -> None:
        if not _has_pillow() or not self._jobs:
            return
        from PIL import Image  # type: ignore[import-not-found]  # optional `images` extra

        img_dir = out_dir / "images"
        img_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.config.root / ".ep" / "svg-tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        for rel, jobs in self._jobs.items():
            src = self.resolve_src(rel)
            if src is None:
                continue
            base, _ext = os.path.splitext(rel)
            digest = file_digest(src, 10)
            # Skip sources whose outputs already exist (incremental / dev caching)
            outputs = [img_dir / f"{base}-{digest}-{w}.{ext}" for (w, ext) in jobs]
            if all(o.exists() for o in outputs):
                continue
            try:
                raster = (
                    self._rasterize_svg(src, tmp) if src.suffix.lower() == ".svg" else src
                )
                if raster is None:
                    print(f"  [epresso] skipped image (cannot process): {rel}")
                    continue
                im = Image.open(raster)
                for w, fmt in sorted(jobs):
                    ratio = w / im.width
                    h = max(1, round(im.height * ratio))
                    resized = im.resize((w, h), Image.Resampling.LANCZOS)
                    if im.mode in ("RGBA", "P"):
                        resized = resized.convert("RGBA")
                    else:
                        resized = resized.convert("RGB")
                    ext, _ = FORMATS[fmt]
                    out = img_dir / f"{base}-{digest}-{w}.{ext}"
                    out.parent.mkdir(parents=True, exist_ok=True)
                    resized.save(out, fmt.upper(), quality=82)
            except Exception as e:  # noqa: BLE001
                print(f"  [epresso] image error on {rel}: {e}")
