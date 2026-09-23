---
order: 313
---

# Content collections

Content is data. A collection is a named group of entries, each validated
against an optional Pydantic schema, stored in a collection-keyed immutable
store. The entry digest drives incremental
rebuilds.

## Defining collections

Collections are declared in `content.config.py`:

```python content.config.py
from pydantic import BaseModel
from epresso.content import define_collection, reference

class Post(BaseModel):
    title: str
    date: str
    tags: list[str] = []
    author: reference("authors")   # content reference
    draft: bool = False

posts = define_collection("posts", glob="**/*.md", base="./content/posts", schema=Post)
authors = define_collection("authors", loader=fetch_authors)  # remote/derived
```

`define_collection` requires a `glob` pattern **or** a `loader` function. When
installed, the loader's base is resolved relative to the site root and entries
are loaded and validated against the schema.

## Loaders

* **Glob loader** — `glob="**/*.md", base="./content/posts"` reads files from
  disk. Optionally `generate_id=callable` to derive entry ids from paths.
* **Python loader** — `loader=fetch_authors` is any callable; epresso wraps it
  as a `PythonLoader`. Use it for remote or derived data.

## Content store

The store is a `Map<collection, Map<id, entry>>`. An entry is
`{id, data, filePath, body, digest, rendered}`:

* `entry.data` — validated schema data.
* `entry.slug` / `entry.id` — entry id without extension.
* `entry.headings` — extracted headings (from `rendered.metadata`).
* `entry.digest` — stable digest over body + data; the incremental key.

```python
store.get_collection("posts")        # -> list[Entry] (deterministically sorted by id)
store.get_entry("posts", "hello")    # -> Entry | None
store.collection("posts")            # -> Collection (raw)
store.names()                        # -> sorted collection names
```

## Accessing data in templates and routes

The curated globals mirror the store:

```jinja
{% for post in get_collection("posts") %}
  <a href="/blog/{{ post.id }}/">{{ post.data.title }}</a>
{% endfor %}
```

`get_entry(collection, id)` fetches a single entry. These helpers also **record
the dependency edge** for incremental builds — a change to an entry re-renders
only the pages that consume it.

## Content references

Use `reference("collection")` as a field type to store a referenced entry id as
a string, then resolve at render time with `get_entry(...)` / `get_entries(...)`:

```python
class Post(BaseModel):
    author: reference("authors")
```

## Drafts & scheduled content

In production builds, `draft: true` and future-dated entries are automatically
excluded from output.

## Private files (underscore prefix)

Files and directories whose name starts with `_` (e.g. `_draft.md`, `_partials/`)
are treated as **private** — the Jekyll convention. Most loaders exclude them
from builds (this applies to content collections, `pages/` routes, and `public/`
passthrough).

The **docs loader** instead keeps `_`-prefixed files but tags them **private**,
and honors `draft: true`. In the dev server a coloured status pill shows in the
toolbar (bottom-right) so you know the current page is private or draft.

## Controlling visibility per environment (`[content]`)

Which of these entries actually show up is configurable. By default epresso shows
draft and private entries in **development / preview** and hides them in
**production** builds. Set `[content]` in `site.toml` to change that:

```toml
# site.toml  — the production base (epresso build / preview / check)
[content]
show_drafts  = false   # omit to keep the default (shown in dev, hidden in prod)
show_private = false
```

The keys are optional: when left out, the historic default applies (shown in
development/preview, hidden in production). An explicit value overrides it for
the current environment. Because per-environment files are merged on top of
`site.toml`, you can split dev and prod behaviour across files:

```toml
# site.development.toml  — merged on top for `epresso dev`
[content]
show_drafts  = true
show_private = true
```

```toml
# site.production.toml  — merged on top for `epresso build`/`preview`/`check`
[content]
show_drafts  = false
show_private = false
```

`show_drafts` controls `draft: true` entries; `show_private` controls `_`-prefixed
(private) ones. Both apply to the docs collection (and to any collection whose
schema carries a matching `draft`/`private` field). Future-scheduled dates are
still excluded in production only.

## Data collections

Collections can be backed by JSON / YAML / TOML files as well as Markdown — the
glob loader reads whatever files match, and `schema` validates them. A markdown
post with YAML front matter:

```markdown
---
title: Hello
date: 2026-01-01
tags: [python]
---
# Hello
```

Markdown is rendered to HTML (see [Markdown](markdown.md); the entry's
`rendered.html` and `rendered.metadata` (headings, image paths) are available.
