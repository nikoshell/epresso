---
title: Create a theme
order: 30
description: Structure a project so epresso new can scaffold others from it.
---

A theme is not a special file format. It is a **normal epresso project shaped
for reuse**: the same `components/`, `layouts/`, `styles/`, `pages/` and
`site.toml` you already write, plus two conventions — *everything visual is a
component*, and *site-specific values come from configuration, not from the
theme's own files*.

Use [`themes/docs`](https://github.com/nikoshell/epresso/tree/main/themes/docs)
as the reference implementation.

## 1. Start a project

```bash
epresso init epresso-theme-mytheme
cd epresso-theme-mytheme
```

Name the directory after the theme — a sibling repo named
`epresso-theme-<name>` is exactly what the theme registry looks for when
developing locally (see step 5).

## 2. Adopt the theme conventions

A reusable theme keeps to a shape that makes it predictable to override:

```tree
epresso-theme-mytheme/
  site.toml              # defaults + a [theme] table for options
  layouts/               # page shells (Base.ep, Doc.ep) — expose <slot/>
  components/            # every visual element, grouped by role
    ...
  styles/
    global.css           # design tokens (:root vars), resets, fonts
  pages/
    index.ep             # a starter page, or nothing at all
  content.config.py      # only if the theme owns a collection (e.g. docs)
  README.md              # what the theme provides and which options it reads
```

Rules of thumb:

- **No hard-coded branding.** Names, URLs, menus and accents come from
  `site.toml` (`[site]`) or the theme's own `[theme]` table, never from a
  literal in a component.
- **Global styles live in `styles/`.** Only truly document-wide things —
  tokens, fonts, resets. Everything component-specific goes in that
  component's scoped `<style>`.
- **Layouts use `<style is:global>`.** A shell's styles must not be scoped to
  the shell's own output.
- **Ship a starter, not a site.** One or two example pages are fine; real
  content belongs to the person using the theme.
- **`[theme]` is your options table.** epresso passes it through untouched —
  read it from a component's frontmatter as `site.config.theme`.

## 3. Wire options through `[theme]`

Declare defaults in the theme's `site.toml`:

```toml
[site]
name = "My Theme"
url = "http://localhost:4321"

[build]
trailing_slash = "always"

[assets]
css = ["global.css"]

[theme]
accent = "#087a44"
footer_text = "Built with epresso"
```

Inject a configured value from the layout shell
(`layouts/Base.ep`). A shell is a full HTML document with one
global style block and the content slot:

```epresso
---
---
<!doctype html>
<html lang="{{ site.config.site.language or 'en' }}">
  <head>
    <meta charset="utf-8">
    <title><slot name="title">{{ site.config.site.name }}</slot></title>
    <link rel="stylesheet" href="{{ asset('global.css') }}">
    <style is:global>
      :root { --accent: {{ site.config.theme.get('accent', '#087a44') }}; }
    </style>
  </head>
  <body>
    <main><slot/></main>
    <footer>{{ site.config.theme.get('footer_text', '') }}</footer>
  </body>
</html>
```

A component reads the same table — frontmatter runs with `site` in scope:

```epresso
---
from pydantic import BaseModel

class Props(BaseModel):
    title: str
    subtitle: str = ""
---
<style>
  .hero { padding: 4rem 1rem; text-align: center; }
  .hero h1 { color: var(--accent); }
</style>
<section class="hero">
  <h1>{{ props.title }}</h1>
  {% if props.subtitle %}<p>{{ props.subtitle }}</p>{% endif %}
  {{ content }}
</section>
```

## 4. Test it like a project

A theme is buildable on its own:

```bash
epresso dev .            # live reload
epresso build .          # → dist/
epresso check .          # validate config + routes
epresso fmt .            # canonical .ep formatting
```

Create a scratch site that consumes the theme to check the parts a theme cannot
exercise alone (navigation, missing options, empty collections):

```bash
epresso new mytheme /tmp/consumer
cd /tmp/consumer && epresso dev
```

## 5. Make `epresso new` find it

Register the theme in `src/epresso/themes.py`:

```python
REGISTRY: dict[str, tuple[str, str]] = {
    # name -> (repo path or URL, default branch)
    "docs": ("<repo>/themes/docs", "main"),            # ships in this repository
    "blog": ("...epresso-theme-blog", "main"),           # sibling checkout / git URL
    "mytheme": ("https://github.com/you/epresso-theme-mytheme", "main"),
}
```

The value may be an **in-repo path** (themes that ship with epresso, like
`themes/docs`), a **local path** to a sibling checkout while developing, or a
**published git URL**. Then:

```bash
epresso new mytheme mysite
```

See [Start from a template](guides/themes/from-template.md) for the resolution
order and the failure mode when a theme is unreachable.

> **Note:** registering a theme currently means editing `themes.py`. Publishing a
> theme as an installable package — so consumers add it with their package
> manager instead — is designed but not implemented. It is covered by a *Coming
> soon* tutorial, visible in local previews.

## 6. Document the theme

Your theme's `README.md` is its contract. List:

- the options it reads from `[theme]` (and their defaults),
- the collections it expects, if any,
- the components it exposes for pages to use,
- anything a consumer must keep (e.g. a specific `[assets] css` entry).

## Next steps

- [Start from a template](guides/themes/from-template.md) — what a consumer runs.
- [Components](../basics/components.md) — props, slots, scoped CSS.
- [Plugins](../guides/extending/plugins.md) — if the theme needs template globals
  or filters (ship a `plugins.py`, as `epresso-ui` does).
