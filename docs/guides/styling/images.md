---
order: 322
---

# Images

The image service produces **responsive images** via Pillow (optional, lazily
imported — a text-only site pays nothing). Source images live under `assets/`
(or `public/`, or `content/`).

## Requirements

Pillow is only required when images are actually used:

```bash
pip install "epresso[images]"
```

If Pillow (or the source image) is unavailable, `image()` falls back to a plain
`<img>` pointing at the original asset.

## `image()` — responsive `<img>`

```jinja
<img src="{{ image('photos/hero.jpg', widths=[400, 800, 1200], alt='Hero') }}">
```

Renders a WebP `srcset` with content-hashed filenames. Default widths are
`[400, 800, 1200]`:

```html
<img src="/images/hero-<digest>-1200.webp" srcset="/images/hero-<digest>-1200.webp 1200w, ..." sizes="100vw" alt="Hero">
```

## `picture()` — WebP + JPEG fallback

`picture()` produces a `<picture>` with WebP sources plus a JPEG fallback — useful when you must support browsers without WebP:

```jinja
{{ picture('photos/hero.jpg', widths=[400, 800], alt='Hero') }}
```

## How it works

* `_register(name, widths, formats)` records processing jobs per source image.
* At build time, `ImagePipeline.build(out_dir)` resizes each source with
  `LANCZOS` to the requested widths and formats (`webp` and `jpeg`, quality 82).
* Outputs are written to `dist/images/` with a content-hash digest in the
  filename; existing outputs are skipped (incremental/dev caching).
* Outputs are written under `dist/images/<base>-<digest>-<width>.<ext>`.

## SVG rasterization

SVG sources are rasterized to PNG first so Pillow can process them. epresso
prefers **cairosvg** (needs the system cairo library); otherwise falls back to
the `inkscape` or `rsvg-convert` CLI when available.

## Custom class

`render_cls(name, widths, alt, cls, style="")` is the class-aware variant (used
by component `image` helpers) and renders an `<img>` with the given CSS class and
optional inline style.

## Optimising content images

`image()` is for templates. Images written in Markdown (`![Diagram](img/diagram.png)`)
and plain `<img>` tags are optimised by the `epresso_optimize` plugin, which the
docs theme enables:

```toml
plugins = ["epresso_optimize"]

[plugin.epresso_optimize]
widths = [400, 800, 1200]   # WebP variants, never wider than the source
sizes = "100vw"             # the docs theme uses "(max-width: 46rem) 100vw, 46rem"
quality = 80
```

After a production build, every local PNG/JPEG `<img>` gets WebP variants in
`dist/images/`, a `srcset` and `sizes`, `loading="lazy"`, `decoding="async"` and
its real `width`/`height` (so the page doesn't jump while it loads). The original
file stays as the `src` fallback. GIF, SVG, external images and any `<img>` that
already sets `srcset`, `loading` or `width` are left as written. `epresso dev`
skips it; set `dev = true` to optimise there too. Encoded files are cached in
`.cache/optimize/`.
