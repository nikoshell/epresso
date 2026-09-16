# Styling and CSS

epresso keeps CSS **optional**: a text-only site needs no build tooling. Three
levels of styling are supported.

## 1. Plain CSS via `asset()`

Declare CSS entry points in `[assets]` and link them with the `asset()` helper,
which resolves a content-hashed public URL:

```toml
[assets]
css = ["css/main.css"]
```

```jinja
<link rel="stylesheet" href="{{ asset('css/main.css') }}">
```

`[assets] hash = true` (default) adds a content hash to the filename for caching.

## 2. Scoped CSS in `.ep` components

A `<style>` block in a `.ep` file is extracted and **scoped** to the
component/route's output via a `data-epresso-<hash>` attribute, then written to
`dist/_scoped/epresso-<hash>.css`:

```epresso
---
---
<style>
  .card { border: 1px solid #ccc; }
  :global(.reset) { margin: 0; }  /* opt out of scoping */
</style>
<div class="card">{{ content }}</div>
```

Rules are prefixed with the scoping selector. `:global(...)` rules are stripped
to their inner selector, which stays global (unscoped). Scoped CSS is linked
automatically into any page that uses the component.

## 3. PostCSS / Tailwind

When a project has a PostCSS or Tailwind setup and the corresponding binary is
available, epresso runs it on the declared CSS entry points:

* Detected by the presence of `postcss.config.*` / `tailwind.config.*` (or a
  project-local Tailwind v4 `node_modules/.bin/tailwindcss`).
* Binaries are located from `node_modules/.bin` first, then `PATH`.
* Output is content-hashed like other assets.

If the binary is unavailable, epresso falls back to a verbatim copy, so CSS stays
optional.

## Styling a layer

Components from a [layer](../guides/extending/layers.md) carry their scoped `<style>`
and `<script>` exactly like site components, so a library's per-component styles
work with no extra setup. Global CSS from a layer must travel in a
`<style is:global>` block inside one of its components — v1 layers contribute
`components/` and `layouts/` only, so `asset()` cannot reach a layer's
`styles/` or `assets/`.

## Fonts

There is no dedicated font pipeline — include `@font-face` rules in your CSS or
a `<link>` to a font provider in your layout's `<head>`.

## Syntax highlighting

Fenced code blocks in Markdown are highlighted with **Pygments** by default
(`[markdown] highlight = false` opts out). Include the generated CSS in your
layout:

```jinja
<style>{{ pygments_css() }}</style>
```

## CSS Modules & fonts

There is no CSS-Modules compilation — component styles are **scoped** by the
framework instead (see Scoped CSS above). Fonts have no auto-optimization; self-host
them via `@font-face` in a global stylesheet and `public/`/`asset()` (see [Fonts](fonts.md).
