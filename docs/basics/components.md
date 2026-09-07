# Components

Components are server-rendered, tag-based building blocks. epresso resolves a
component as `components/<Name>.ep` first, then
`components/<Name>.html`, and finally looks under
`layouts/` (so a layout can double as a component).

## The `.ep` file format

`.ep` files unify **Python frontmatter** (`--- … ---`) + **Jinja body** + optional
**scoped `<style>`** + optional **client `<script>`**:

```epresso components/Card.ep
---
from pydantic import BaseModel

class Props(BaseModel):
    title: str
    level: int = 3
---
<div class="card"><h{{ props.level }}>{{ props.title }}</h{{ props.level }}>{{ content }}</div>
```

### Typed props

A `Props` Pydantic model validates props before they reach the template — no
unvalidated kwargs:

```epresso
---
from pydantic import BaseModel

class Props(BaseModel):
    title: str
    level: int = 3
---
<div class="card"><h{{ props.level }}>{{ props.title }}</h{{ props.level }}>{{ content }}</div>
```

Invalid props raise a `TemplateError` at render time. A component is **scoped
only when it contains a scoped `<style>` block**; a `.ep` file with no scoped
CSS (or only `<style is:global>`) renders unscoped, so a layout shell needs no
flag (see [Layouts](layouts.md).

## Using a component

Two equivalent syntaxes.

**Jinja tag:**

```jinja
{% component "Card", title="Hi", level=2 %}Body text{% endcomponent %}
```

**JSX-style tags** (rewritten to `{% component %}` before parsing):

```jinja
<Card title="Hi">Body text</Card>
```

* Only tags that resolve to a registered component are converted — `<div>`,
  `<section>`, etc. pass through as plain HTML.
* Attributes: `key="value"` (string), `key={expr}` (expression), or a bare `key`
  (boolean `true`).
* Paired components take children as `{{ content }}`; children may nest more
  components.
* The legacy `{% component %}` tag still works and can be mixed freely.

### Slots

Components get a **default slot** (`{{ content }}`, the children) plus **named
slots**:

```jinja
<Card title="Hi">
  <Fragment slot="header">Header content</Fragment>
  Default body content
</Card>
```

```epresso
---
---
<div class="card"><h3>{{ props.title }}</h3><header>{{ slot('header') }}</header>{{ content }}</div>
```

Use `{{ slot('name') or 'fallback' }}` for fallback content. Works for `.ep` and
`.html` components.

## Scoped CSS

A `<style>` block in a `.ep` file is extracted, scoped to the component's output
(via a `data-epresso-<hash>` attribute), and linked from the head:

```epresso
---
---
<style>
  .card { border: 1px solid #ccc; }
  :global(.reset) { margin: 0; }  /* opt out of scoping */
</style>
<div class="card">{{ content }}</div>
```

Scoped CSS is written to `dist/_scoped/epresso-<hash>.css`. `:global(...)` rules are
stripped to their inner selector, which stays global (unscoped). See [Styling and CSS](../guides/styling/styling.md.

## Template syntax

The `.ep` body is a Jinja template: expressions, conditionals and loops interleave
with HTML, and attribute values can be expressions.

### Expressions

`{{ … }}` outputs a value; attributes accept `{expr}`:

```epresso
<h1>{{ props.title }}</h1>
<p class="{{ props.description ? 'has-desc' : '' }}">…</p>
<a href="/{{ props.slug }}/">read</a>
```

Every component has `props` (the validated Pydantic model), plus `site`, `content`
(slot children), and any frontmatter helpers you define.

### Conditionals

`{% if %}` / `{% elif %}` / `{% else %}` render a branch when the expression is
truthy:

```epresso
{% if props.prev %}
  <a href="{{ props.prev.url }}">← {{ props.prev.title }}</a>
{% else %}
  <span>This is the first page.</span>
{% endif %}
```

### Loops

`{% for x in seq %}` iterates a list (array indices via `loop.index`):

```epresso
<ul>
{% for h in props.headings %}
  <li><a href="#{{ h.slug }}">{{ h.text }}</a></li>
{% endfor %}
</ul>
```

### Comments

`{# … #}` are comments and are not rendered.

## Client scripts

A `<script>` block in a `.ep` file is extracted, bundled with esbuild (falling
back to a raw module when esbuild isn't installed), and loaded on pages that use
the component:

```epresso
---
---
<script>
  document.querySelector('.count').addEventListener('click', () => alert('hi'));
</script>
<button class="count">{{ content }}</button>
```

Identical script blocks dedupe to one bundle under `dist/_epresso/scripts/`.

## Markdown components

Allow-listed component tags can be used directly in Markdown (see
[Markdown](../guides/content/markdown.md). `md/` wrapper components take precedence so a
markdown-facing interface can differ from the underlying component (e.g. a
`<YouTube id>` → blocks/YouTube wrapper).

## Plain `.html` components

Backwards-compatible plain Jinja templates under `components/`. They
receive kwargs plus `content`, `slots`, `slot()`, and `site`.

## Compose with components, not Jinja composition

Composition in `.ep` is done with component tags and `<slot/>` — not with
Jinja's structural directives. `{% extends %}`, `{% block %}`, `{% include %}`,
`{% component %}`, `{% import %}`/`{% from … import %}`, `{% macro %}` and
`{% call %}` are **rejected** in `.ep` files at load time: the build fails with
the file, line and directive named.

- Replace `{% extends %}` + `{% block %}` with a **layout component** that emits
  the HTML shell and exposes `<slot/>` (e.g. `layouts/Base.ep`), then write
  `<Base title={…}>…content…</Base>`.
- Replace `{% include %}` / `{% component %}` with `<Component/>`.
- Replace `{% macro %}` / `{% import %}` with a component + props.

Still allowed in `.ep`: `{{ expr }}` interpolation, JSX props (`{expr}`),
`{% if %}` / `{% for %}` control flow, comments, and `<slot/>`. Plain `.html`
components/templates keep full Jinja and are unaffected.
