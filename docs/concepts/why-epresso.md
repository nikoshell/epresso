# Why epresso?

epresso is a **Python-first static site generator**. It brings the content-first,
component-based model of modern static-site frameworks to Python authors:
content collections with typed schemas, code-as-routes pages, scoped CSS, and
no-JavaScript-by-default output — all expressed in Python rather than JSX/TS.

- **Routes-as-code**: files under `pages/` are code, not opaque config. A `.ep`
  page has a Python frontmatter that can export `get_static_paths()` for dynamic
  routes.
- **Content collections** with typed schemas and deterministic loaders.
- **Deterministic + incremental builds**: content digests drive a build graph so
  unchanged pages are served from cache.
- **No JavaScript by default**: server-rendered HTML; JS is opt-in per component.

Use it when you want content-first static sites and would rather write Python.
