---
order: 250
---

# Performance

epresso is designed for fast static sites:

- **No JavaScript by default** — pages are plain HTML, so first load is minimal.
- **Incremental builds** — a build graph keys routes to content digests; when a
  document changes, only its dependents rebuild (others are served from cache).
- **Dedup + minification** — repeated scoped CSS/client scripts collapse to one
  asset; HTML/CSS are minified.
- **Content-hashed assets** via `asset()` for cache-friendly URLs.

For runtime performance, ship little/no JS (the default) and follow the
[Images](guides/styling/images.md) and [Fonts](guides/styling/fonts.md) guidance.
