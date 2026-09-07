# Layouts

Layouts wrap page content in a shared HTML shell. epresso supports two models:
classic Jinja **inheritance** with blocks, and **layout components**.

## Jinja inheritance (block-based)

The most common convention. A layout is a template with `{% block %}` slots;
pages `{% extends %}` it and fill blocks.

`layouts/base.html`:

```jinja
<!doctype html><html><head>
  <meta charset="utf-8">
  <title>{% block title %}epresso{% endblock %}</title>
  {% block head %}{% endblock %}
</head><body>
  {% block content %}{% endblock %}
</body></html>
```

A Markdown page fills the `content` block via its front-matter `layout`:

```markdown
---
layout: base.html
title: About
---
# About
```

A `.ep` route does the same with Jinja tags:

```epresso
---
---
{% extends 'base.html' %}
{% block title %}{{ props.title }}{% endblock %}
{% block content %}<h1>{{ props.title }}</h1>{{ content | safe }}{% endblock %}
```

Markdown pages are wrapped automatically: a child template extends the layout
and fills its `content` block with the rendered Markdown HTML.

## Layout components

A `.ep` component is **scoped only when it contains a scoped `<style>` block**
— it is then wrapped in a `data-epresso-*` div and its selectors are rewritten.
A component with no scoped CSS (or only `<style is:global>`) renders
**unscoped** (no wrapper). So a layout shell that emits a full `<!doctype html>`
document is automatically unscoped:

```epresso
---
---
<!doctype html><html><head><title>{{ title }}</title></head>
<body>{{ content }}</body></html>
```

Make any layout `<style>` global with `<style is:global>` (or by linking a
global stylesheet) rather than a scoped `<style>`.

```jinja
<BaseLayout title={title}>
  <Header />
  <main>…</main>
  <Footer />
</BaseLayout>
```

Layout components may live in `layouts/` (resolved as a component in
addition to `components/`), so `BaseLayout` stays alongside your
layouts while being composed as a component.

### Slots (`<slot />`)

A layout component can declare `<slot />` (default content) and
`<slot name="X" />` (named) placeholders, filled by the page with
`<Fragment slot="X">…</Fragment>` — named slots:

```epresso
# layouts/Page.ep
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

```jinja
# pages/about.ep
{% component "Page" %}
  <Fragment slot="title">About</Fragment>
  <Fragment slot="header"><nav>…</nav></Fragment>
  <h1>About us</h1>
  <p>Body → default <code>&lt;slot /&gt;</code>.</p>
  <Fragment slot="footer"><small>© 2026</small></Fragment>
{% endcomponent %}
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
`render_md()`, `fmt_dt()`, `pygments_css()`, `env`, `env_vars`, and more — see
the [template syntax reference](routing.md#route-object.
