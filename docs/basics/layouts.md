---
order: 150
---

# Layouts

Layouts wrap page content in a shared HTML shell. A layout is a **layout
component**: an `.ep` file that emits the document (or a region) and exposes
`<slot/>` placeholders.

Layouts live in the top-level `layouts/` directory. Because `layouts/` is a
component root, any `.ep` file there can also be used as a component from
another template.
Layouts can also come from a [layer](guides/extending/layers.md) — another
repo, package or directory — with the site's own `layouts/` always searched
first.

> `.html` layout templates are not supported: a layout is always a `.ep`
> component. `{% extends %}`/`{% block %}` are rejected in `.ep` files — compose
> with `<slot/>` instead.

## Writing a layout

A layout is a normal `.ep` component. A document shell emits a full
`<!doctype html>` document; because it declares no scoped `<style>`, it renders
**unscoped** (no wrapper element):

```epresso layouts/Base.ep
---
from pydantic import BaseModel

class Props(BaseModel):
    title: str = ""
---
<!doctype html>
<html lang="{{ site.config.site.language }}">
  <head>
    <meta charset="utf-8">
    <title>{{ props.title }}</title>
  </head>
  <body><slot /></body>
</html>
```

Make any layout `<style>` global with `<style is:global>` (or by linking a
global stylesheet) rather than a scoped `<style>`.

## Using a layout

A `.ep` route composes it as a component:

```epresso pages/about.ep
---
---
<Base title="About">
  <header><nav>…</nav></header>
  <main><h1>About us</h1></main>
  <Footer />
</Base>
```

A **Markdown** page names it in front matter:

```markdown pages/about.md
---
layout: Base
title: About
---
# About us
```

`layout:` accepts the component name — `Base`, `layouts/Base` or `Base.ep` all
resolve to `layouts/Base.ep`. The page title is passed both as a `title` prop
and as a `<slot name="title" />` fragment, and the rendered Markdown is the
default slot. A Markdown page with no `layout:` renders as a minimal standalone
document.

Layout components may live in `layouts/` (resolved as a component in addition to
`components/`), so `Base` stays alongside your layouts while being composed as a
component.

## Slots (`<slot />`)

A layout component can declare `<slot />` (default content) and
`<slot name="X" />` (named) placeholders, filled by the page with
`<Fragment slot="X">…</Fragment>`:

```epresso layouts/Page.ep
---
---
<!doctype html><html><head>
  <title><slot name="title" /> · {{ site.config.site.name }}</title>
  <slot name="head" />
</head><body>
  <header><slot name="header" /></header>
  <main><slot /></main>
  <footer><slot name="footer" /></footer>
</body></html>
```

```epresso pages/about.ep
---
---
<Page>
  <Fragment slot="title">About</Fragment>
  <Fragment slot="header"><nav>…</nav></Fragment>
  <h1>About us</h1>
  <p>Body → default <code>&lt;slot /&gt;</code>.</p>
  <Fragment slot="footer"><small>© 2026</small></Fragment>
</Page>
```

`<slot name="X">fallback</slot>` (non-empty body) renders the fallback when the
slot is empty. Named-slot fragments are removed from the default content, so
text interleaved between them is preserved.

> `<style>` in a page is always treated as page-scoped CSS — to inject a
> stylesheet into a `<slot name="head">`, put it in the layout (or a
> component) instead of a page's `<Fragment>`.

## Curated globals available in layouts

`site`, `url()`, `asset()`, `image()`, `picture()`, `seo()`,
`get_collection()`, `get_entry()`, `route`, `params`, `props`, `content`,
`render_md()`, `fmt_dt()`, `pygments_css()`, `env`, `env_vars`,
`epresso_version`, and more — see
the [template syntax reference](routing.md#route-object.
