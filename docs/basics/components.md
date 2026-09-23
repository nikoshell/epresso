---
order: 140
---

# Components

Components are server-rendered, tag-based building blocks. epresso resolves a
component as `components/<Name>.ep` first, then looks under `layouts/` (so a
layout can double as a component).

Components from an external repo or directory can be layered in with
[`[layers] use`](guides/extending/layers.md); the site's own files are always
searched first, so a site component with a matching basename overrides the
layer's.

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

### File shape — one root per branch

An `.ep` file renders **at most one root** per branch — a branch may render
nothing (an `{% if %}` with no `{% else %}`, a `{% for %}` over an empty
sequence, an empty array). A root is anything that emits output: an element, a
component, `<slot/>`, `<Fragment>`/`<>`, an interpolation (`{{ … }}`) or text.
Whitespace and comments emit nothing, so they are ignored; `{% if %}` /
`{% for %}` introduce *branches*, and each branch is checked the same way.

```epresso
---
---
<Fragment>                        <!-- ❌ two siblings at the top level -->
<div class="a">a</div>
<aside>b</aside>
</Fragment>                        <!-- ✅ one root: the group -->
```

Patterns:

| need | write |
|---|---|
| group siblings, render no wrapper | `<Fragment>…</Fragment>` or `<></>` |
| a branch that renders *nothing* | `{% if x %}<a>…</a>{% endif %}` — no `{% else %}` needed; an empty branch is fine |
| forward the caller's content | `<slot/>` (a root in its own right) |
| conditionally forward | `{{ content }}` counts as one root (it is treated as `<Fragment>{{ content }}</Fragment>`) |

The sidecars are capped **per kind** too: at most one scoped `<style>`, one
`<style is:global>` and one `<script>` per file — merge same-kind blocks.

Violations fail the build with file, line and a fix hint. `.ep` endpoints (whose
body is never rendered) are exempt.

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

### Same basename in different subdirectories

A component is normally found by basename alone, wherever it lives under
`components/` (`components/Card.ep`, `components/controls/Card.ep`, `components/ui/anything/Card.ep`
all answer to `<Card />`). If two files share a basename outside the
`components/`/`layouts/` roots themselves, which one `<Card />` resolves to is
undefined — pick a specific one with `<Name:dir />`:

```jinja
<A:comp1 />   {# components/comp1/A.ep #}
<A:comp2 />   {# components/comp2/A.ep #}
<A:dir1:dir2 />  {# components/dir1/dir2/A.ep #}
```

The qualifier goes after the name (not before, XML-namespace style) because a
tag must start with an uppercase letter to be recognized as a component at
all — `<comp1:A />` would just look like an unrecognized lowercase HTML tag.
The same call also works through the low-level tag: `{% component "A:comp1" %}`.

### Slots

Components get a **default slot** (`{{ content }}`, the children) plus **named
slots**:

```jinja
<Card title="Hi">
  <Fragment slot="header">Header content</Fragment>
  Default body content
</Card>
```

`slot="…"` also works directly on any element, which slots that element (and its
subtree) without a wrapper — the marker attribute is stripped from the output:

```jinja
<Panel>
  <img slot="side" src="/a.png" alt="">
  Body content
</Panel>
```

Use a slot-less `<Fragment>` (or `<></>`) to group siblings without emitting an
element — the group still counts as the file's one root (see
[File shape](#file-shape-one-root-per-branch)).

```epresso
---
---
<div class="card"><h3>{{ props.title }}</h3><header>{{ slot('header') }}</header>{{ content }}</div>
```

Use `{{ slot('name') or 'fallback' }}` for fallback content.

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
[Markdown](guides/content/markdown.md). `md/` wrapper components take precedence so a
markdown-facing interface can differ from the underlying component (e.g. a
`<YouTube id>` → blocks/YouTube wrapper).

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
`{% if %}` / `{% for %}` control flow, comments, and `<slot/>`.
