# Pages

A page is any file under `pages/` that produces one or more URLs. epresso maps
filesystem paths to routes; the file kind determines how it renders.

| File | Kind |
|------|------|
| `pages/about.md` | Direct Markdown page (layout via front matter) |
| `pages/about.ep` | Single-file route (Python frontmatter + Jinja body) |
| `pages/blog/[slug].ep` | Dynamic `.ep` route via `get_static_paths()` |
| `pages/blog/[slug].html` + `[slug].py` | Template route + sidecar (legacy) |
| `pages/robots.txt.py` | Endpoint exporting `get() -> (content_type, body)` |

## Clean URLs

Directories and dynamic segments map to clean directory URLs with a configurable
trailing slash (`[build] trailing_slash`):

```
pages/index.ep            → /
pages/about.md            → /about/
pages/blog/[slug].ep      → /blog/<slug>/
pages/blog/[slug]/index.ep → /blog/<slug>/
pages/blog/[...slug].ep   → /blog/a/b/   (spread)
```

## `.ep` routes (recommended)

An `.ep` page combines Python frontmatter + a Jinja body in one file. The
frontmatter can export `get_static_paths()` to render multiple URLs, or `get()`
for a static endpoint. See [Routing](routing.md and [The `.ep` file format](components.md.

## Private files

Files and directories whose name starts with `_` (e.g. `_draft.ep`, `_partials/`)
are treated as private and **excluded from builds** — see [Content collections](../guides/content/content-collections.md.
