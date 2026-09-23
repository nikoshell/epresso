---
order: 361
description: Scaffold an empty epresso project and add your first page and component.
---

# Create a new website

Start from nothing. This gives you the standard project layout and no opinions
about content or styling.

## 1. Scaffold

```bash
epresso init mysite
cd mysite
```

`init` creates:

```tree
mysite/
  site.toml            # configuration
  content.config.py    # collection definitions (empty template)
  content/             # collection data (markdown / JSON / YAML / TOML)
  pages/               # routes
    index.ep
  layouts/
    Base.ep            # the HTML shell, exposes <slot/>
  components/          # reusable components
  styles/              # global stylesheets
  public/              # files copied verbatim to the output root
```

Build it immediately:

```bash
epresso build          # ✅ Built 1 pages … → dist/
epresso dev            # http://127.0.0.1:4321, live reload
```

## 2. Make it yours

Edit `site.toml` — at minimum the name and URL:

```toml
[site]
name = "My Site"
url = "https://example.com"
language = "en"

[build]
trailing_slash = "always"
```

`pages/index.ep` is a single file: Python frontmatter between `---` fences,
then a Jinja body. It renders inside `layouts/Base.ep` through the `<Base>`
component:

```epresso
---
---
<Base title={site.config.site.name}>
<h1>Hello, epresso!</h1>
<p>This is your first page.</p>
</Base>
```

## 3. Add a page

Create `pages/about.ep`:

```epresso
---
---
<Base title="About">
<h1>About</h1>
<p>Written in a single file.</p>
</Base>
```

It becomes `/about/` automatically — the filesystem path *is* the route. See
[Pages](basics/pages.md) and [Routing](basics/routing.md) for dynamic
routes (`[slug].ep`), endpoints (`.py`) and direct Markdown pages (`.md`).

## 4. Add a component

A component is also one file, but it may declare a typed `Props` model and a
scoped `<style>` block:

```epresso
---
from pydantic import BaseModel

class Props(BaseModel):
    title: str
    href: str = ""
    featured: bool = False
---
<style>
  .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; }
  .card.featured { border-color: rebeccapurple; }
</style>
<article class="card{% if props.featured %} featured{% endif %}">
  <h2>
    {% if props.href %}<a href="{{ props.href }}">{{ props.title }}</a>
    {% else %}{{ props.title }}{% endif %}
  </h2>
  {{ content }}
</article>
```

Save it as `components/Card.ep` and use it from any page:

```epresso
<Card title="Hello" href="/about/" featured>
<p>Body text goes in the default slot.</p>
</Card>
```

The `<style>` is **scoped to the component's output** — it is not global CSS,
and it is only linked into pages that actually render the component. See
[Components](basics/components.md) for props validation, named slots and
`<style is:global>`.

## 5. Wire in global CSS

Global styles belong in `styles/`. Point `[assets]` at your entry point and link
it with `asset()`:

```toml
[assets]
css = ["global.css"]
```

```epresso
---
---
<!doctype html><html lang="{{ site.config.site.language }}">
<head>
  <meta charset="utf-8">
  <title>{{ props.title }}</title>
  <link rel="stylesheet" href="{{ asset('global.css') }}">
</head>
<body><main><slot/></main></body></html>
```

## 6. Check and build

```bash
epresso check          # validate config + content, list routes
epresso fmt .          # format .ep files to the canonical structure
epresso build          # deterministic output in dist/
epresso preview        # build then serve dist/ exactly as deployed
```

## Next steps

- [Content collections](guides/content/content-collections.md) — typed
  collections with Pydantic schemas.
- [Styling and CSS](guides/styling/styling.md) — assets, PostCSS/Tailwind,
  and when to use scoped CSS.
- [Plugins](guides/extending/plugins.md) — add template globals, filters and
  rendered-output transforms.
