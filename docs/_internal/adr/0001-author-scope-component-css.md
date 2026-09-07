# 1. Scoped CSS follows authorship, not the rendering consumer

Status: Accepted

Date: 2026-09-04

## Context

epresso scoped a component's `<style>` to the elements **rendered inside it**:
the first scoped component to emit an element stamped it with its own scope. Slot
content a caller passed into a child arrived *unscoped*, so the **child** stamped
it — meaning a caller could not style markup it authored and passed into a child
component with its own scoped CSS.

A concrete case forced the issue: `SearchButton` authors a `<kbd>Ctrl K</kbd>`
and passes it into the shared `IconButton` primitive. Under consumer-scoping the
`<kbd>` carried `IconButton`'s scope, so `SearchButton` could never style it with
scoped CSS (only `:global`). Modern component frameworks solve this by scoping
CSS to **whoever authors the element**.

## Decision

Make component CSS scope follow **authorship** — scope to the author of an
element, not the rendering consumer:

- An element's scope is the component whose template **wrote** it.
- When a component passes children/slot content into another component, that
  content keeps the **caller's (author's)** scope; the receiver never re-stamps it.
- Rendering tracks an author-scope stack; the `{% component %}`/JSX caller body is
  tagged with the top-of-stack scope before being handed to the child. The scoped
  CSS engine already skips elements carrying `data-epresso-*`, so a receiver only
  scopes the elements it actually authors.

Practical rules this establishes:
- A component styles **only what it authors**. To style inner content it receives,
  style that content where it is authored (or use a shared/global rule).
- A caller can style markup it passes into a child (e.g. `SearchButton` owns the
  keycap look).

## Consequences

Positive:
- Mirrors the author-scoping model developers expect from component frameworks.
- Callers can style their own passed-in content with scoped CSS.

Negative / migration:
- The docs theme's primitives could no longer style caller-authored SVGs
  (`IconButton.ep`'s `.icon-btn svg`) or the keycap — these moved to a shared
  global rule (`.icon-btn svg`) and into the author (`SearchButton.ep`).
- Components that intentionally style content they receive must use `:global()`,
  a `<style is:global>`, or a shared global stylesheet.
- The change is hard to reverse: it flips the scope model site-wide.

## Alternatives considered

1. **Keep consumer-scoping** — simplest, but leaves the keycap (and any
   author-styled passed content) needing `:global`; diverges from author-scoping.
2. **Per-component `:global` escape hatches** — solves each case ad hoc without a
   coherent model; no authorship guarantee.

## Decision drivers

- Author-scoping keeps components self-contained (the target model for the
  docs theme / component styling).
- Enabling components to style content they author and pass to children.
