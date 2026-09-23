# 3. A layer contributes components and layouts only

Status: Accepted

Date: 2026-09-19

## Context

`[layers] use` imports external component/layout roots from a directory, an
installed package, or a git repo. A layer is shaped like a site root, so the
question is how much of a site it may contribute: only the component roots, or
`pages/`, `content/`, `styles/`, `assets/` and `site.toml` as well — an
inheritable theme.

## Decision

In v1 a layer contributes only `components/` and `layouts/`. It does not
contribute `pages/`, `content/`, `styles/`, `assets/` or `site.toml`. Global CSS
a layer needs must travel inside a component's `<style is:global>`.

The seam is the Jinja loader searchpath: `build_environment()` appends each layer
root *after* the site's own roots, and `components._resolve_component_uncached()`
treats every loader root as `<base>/components` plus `<base>/layouts`. The site's
own files are therefore always searched first and shadow a layer's.

## Consequences

Positive:
- One override rule, stated once: site first, then layers in declaration order.
- No merge semantics for content or pages, which have no obvious per-file
  "site wins" analogue.
- A layer can be a plain component library with no build system of its own.

Negative / migration:
- A layer cannot ship global styles or assets directly; they must be packaged in
  a component's `<style is:global>`.
- A layer's utility classes cannot be scanned from the consumer's project
  (Tailwind/UnoCSS), so a layer that uses utilities must ship prebuilt CSS.
- A theme is not usable as a layer. Themes are scaffolded (copied) by
  `epresso new`; layers are imported at build time. Widening layers to styles
  (R2) and page inheritance (R3) remains open in
  `plans/2026-09-15-external-component-import.md`.

## Alternatives considered

1. **Full theme inheritance through layers** — one mechanism for component
   libraries, style layers and themes. Rejected for v1: content and pages need
   merge rules that do not exist, and bundled styles collide with the consumer's
   utility-CSS scan.
2. **Layers contribute styles and assets too (R2 only)** — closer to a theme, but
   it forces a CSS build/scoping decision that the prebuilt-CSS rule already
   answers more simply.

## Decision drivers

- Keep the extension seam small and predictable: the Jinja loader searchpath.
- Ship the component-library half now; defer inheritance until its merge rules are
  designed rather than guessing them.
