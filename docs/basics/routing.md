---
order: 130
---

# Routing

epresso uses **routes-as-code**: every file under `pages/` becomes one or more
routes. Content stays in `content/`; `pages/` produces URLs.

## Page kinds

| File | Kind |
|------|------|
| `pages/about.md` | Direct Markdown page (layout via front matter) |
| `pages/blog/[slug].ep` | Single-file route (Python frontmatter + Jinja body) |
| `pages/robots.txt.py` | Endpoint exporting `get() -> (content_type, body)` |

## Route parts

Path segments support static text, `{param}`, and `{...param}` (spread):

```
pages/blog/index.md          → /blog/
pages/blog/[slug].ep         → /blog/<slug>/
pages/blog/[slug]/index.ep   → /blog/<slug>/   (index.ep = directory root)
pages/blog/[...slug].ep      → /blog/a/b/     (spread captures the rest)
```

`index` in a filename maps to the directory root. Clean directory URLs are
generated with a configurable trailing slash (`[build] trailing_slash`).

## Endpoints

A `.py` page that exports `get()` becomes a static endpoint:

```python pages/robots.txt.py
def get():
    return "text/plain", "User-agent: *\nAllow: /\n"
```

File-style URLs like `/robots.txt` skip the trailing slash. `data.json` and RSS
feeds are commonly built this way.

## `.ep` single-file routes

The recommended route format — Python frontmatter + Jinja body in one file. See
[The `.ep` file format](components.md.

```epresso
---
from epresso.routing import Route

def get_static_paths():
    return [Route(path=f"/blog/{p.id}/", params={"slug": p.id}, data=p)
            for p in site.get_collection("posts")]
---
<article><h1>{{ props.title }}</h1>{{ content | safe }}</article>
```

A static `.ep` route with no `get_static_paths()` renders once at its default path.

`site` is injected into the frontmatter. A returned `Route` carries `path`,
optional `params`, `data` (the props passed to the template), and an optional
`cache_key` (auto-derived from a content entry's digest when absent, so edits
re-render only that path).

## Pagination

`paginate` is a helper that splits entries into numbered page routes:

```python
from epresso.routing import paginate

def get_static_paths():
    return paginate(site.get_collection("posts"), per_page=10, base_path="/blog/")
```

It produces `base_path/` and `base_path/page/N/`, each route carrying
`data={"entries", "page", "num_pages", "prev", "next"}` and `params={"page": n}`.

## Route object

```python
from epresso.routing import Route

Route(
    path="/blog/hello/",
    params={"slug": "hello"},
    data={...},                          # props passed to the template
    content_type="text/html",
    body=None,                           # raw body for endpoints
    cache_key=None,                      # incremental identity
)
```

## Importable helpers

`discover_route_patterns(pages_dir)`, `expand_pattern(pattern, trailing, data_api)`,
`parse_route(path)`, `output_path_for(route_path)`, and `paginate(...)` are all
exported from `epresso.routing` for programmatic use.

## View transitions & prefetch

epresso is a static, multi-page site — links cause a normal full-page navigation.
There are no view-transition or prefetch primitives; every URL is a real HTML
document you can deep-link and cache. Add client-side niceties (transition
animations, link prefetch) yourself in a component `<script>`.
