---
title: Coming soon
order: 90
draft: true
description: Partly shipped, partly designed ways to reuse themes and component libraries.
---

> **Partly available.** Component and layout layers ship today — see
> [Layers](guides/extending/layers.md). The full *theme* layer mode below
> (`styles/`, `pages/`, `site.toml` defaults) is still designed, not
> implemented. These pages render in `epresso dev` previews and are excluded
> from production builds; commands marked *planned* do not work yet.

Both planned features rest on one mechanism: **layers**.

A layer is a directory shaped like a site root. A shipped layer contributes
`components/` and `layouts/`; the planned theme layer additionally contributes
`styles/`, `pages/` and `site.toml` defaults. The site's own files always win.

```
site/            ← your project: wins over everything
  components/ layouts/ styles/ pages/ site.toml
─────────────────────────────────────────────
layer: theme     ← (planned) layouts, styles, pages, site.toml defaults
─────────────────────────────────────────────
layer: library   ← components/ (shipped), styles/tokens.css (planned)
```

`epresso-ui` sits above `epresso-components`, so the styled `<Button>` wins over
the unstyled one whenever the UI layer is present — the skin is a layer, not a
copy.

| Tutorial | What it covers |
|---|---|
| [Use a theme as a layer](guides/themes/planned/use-a-theme.md) | (planned) Reuse a theme without copying it, and override only what you want. |
| [Build with components only](guides/themes/planned/components-only.md) | Take components from a library; keep your own layout and pages. Components layer in today; layer stylesheets are planned. |

## What works today

- **Component / layout layers** — declare a repo, package or directory in
  `[layers] use` and use its components:
  [Layers](guides/extending/layers.md).
- **Whole theme?** Copy it — [`epresso new`](guides/themes/from-template.md) —
  and treat upstream changes as manual merges. Inheriting a theme's `pages/`,
  `styles/` and `site.toml` as a layer is the planned
  [Use a theme as a layer](guides/themes/planned/use-a-theme.md) mode.
