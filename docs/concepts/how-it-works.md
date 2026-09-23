---
order: 220
---

# How epresso works

epresso is a **build-time static generator**:

1. **Config** — `site.toml` (per-env overrides via `site.<env>.toml` + `.env`).
2. **Content** — collections defined in `content.config.py` are loaded by loaders
   into a typed store (`ContentStore`); each entry gets a content digest.
3. **Pages** — every file under `pages/` is a route. `.ep` pages/frontmatter can
   export `get_static_paths()` to fan out many routes from one file.
4. **Build graph** — routes and their content dependencies are tracked so the
   build is incremental: only what changed re-renders.
5. **Render** — Markdown/`.ep` render to HTML with scoped CSS + optional client
   scripts; outputs are deduplicated and minified.
6. **Output** — `dist/` plus generated `sitemap.xml`, `robots.txt`, `llms.txt`, search index.

`epresso dev` serves the same render path with live reload; `epresso build` writes
`dist/`.
