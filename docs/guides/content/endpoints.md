# Endpoints

An endpoint is a page that returns a non-HTML response (JSON, XML, plain text,
etc.) instead of rendering a template. It's defined by a `.py` page exporting a
`get()` function, or an `.ep` page whose frontmatter exports `get()`.

## Python endpoint

`pages/robots.txt.py`:

```python
def get():
    return "text/plain", "User-agent: *\nAllow: /\n"
```

`get()` returns `(content_type, body)`. File-style paths (like `/robots.txt`)
skip the trailing slash.

## `.ep` endpoint

An `.ep` file whose frontmatter exports `get()` is an endpoint too —
e.g. `pages/rss.xml.ep`:

```epresso
---
def get():
    items = [{"title": d.data.title, "url": f"/docs/{d.id}/"} for d in site.get_collection("docs")]
    return "application/rss+xml", site.rss(title="Docs", description="", path="/rss.xml", items=items)
---
```

## Useful helpers

- `site.rss(title, description, path, items)` builds an RSS/Atom feed (the
  output is XML-escaped).
- Endpoints participate in the build graph like any other route.
