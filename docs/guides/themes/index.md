---
title: Themes & templates
order: 60
description: Start a site from scratch, from a ready-made theme, or build one for others to reuse.
---

There are two things you can reuse from another repository, and they are not the
same:

- A **theme** — a whole site: layouts, components, styles, starter pages and
  default configuration. A theme decides *how your site looks and is put
  together*.
- A **component library** — a set of components (and usually a token stylesheet)
  that you drop into a site you are already building. A library does not decide
  your pages or your layout shell.

Pick the path that matches what you want:

| Goal | Tutorial | Status |
|---|---|---|
| Start with an empty project and build it up myself | [Create a new website](guides/themes/new-website.md) | ✅ Available |
| Start from a ready-made theme (docs, blog) | [Start from a template](guides/themes/from-template.md) | ✅ Available |
| Make a theme other people can use | [Create a theme](guides/themes/create-a-theme.md) | ✅ Available |
| Use a theme but keep overriding parts of it and get upstream updates | Use a theme as a layer | 🚧 Planned |
| Use only a component library, with my own layout | [Layers](guides/extending/layers.md) | 🟡 Components available |

**Status legend.** ✅ shipped; 🟡 partly shipped — component and layout layers
work today, layer stylesheets and whole-theme layers do not; 🚧 designed but
unimplemented. The 🟡/🚧 tutorials are drafts: they render in `epresso dev`
previews (look for the **Coming soon** group in the sidebar) and are excluded
from production builds.

## Which should I pick?

- **Nothing to override, want a running site now** → a template
  (`epresso new`). You own a full copy; upstream changes are yours to merge.
- **Want a bigger say in structure** → start blank (`epresso init`) and layer in
  a component library with `[layers] use` — see
  [Layers](guides/extending/layers.md).
- **Building something for others** → author a theme; see
  [Create a theme](guides/themes/create-a-theme.md).

Under the hood all four reuse the same building blocks — `components/`,
`layouts/`, `styles/` and `pages/` — so anything you learn in one tutorial
applies to the others.
