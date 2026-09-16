---
title: Use a theme as a layer
order: 10
draft: true
description: Reuse a theme without copying it, overriding only the files you choose.
---

> **Partly available.** Component and layout layers ship today — see
> [Layers](guides/extending/layers.md). The full theme-as-a-layer mode described
> here (`styles/`, `pages/`, `site.toml` defaults) is still planned. Use
> [`epresso new`](guides/themes/from-template.md) to copy a theme today.

Instead of copying a theme into your project, declare it as a **layer**. Your
files stay on top; the theme fills in everything you have not overridden.

## Declare the layer

```toml
# site.toml
[layers]
use = [
  "git+https://github.com/nikoshell/epresso-theme-docs@v1",
]
```

Then build as usual:

```bash
epresso dev
epresso build
```

The theme contributes its `components/`, `layouts/`, `styles/`, `pages/` and
`site.toml` defaults. You write only what you want to change:

```tree
mysite/
  site.toml                 # your [site], [assets] — wins over the layer's
  components/
    layouts/
      Base.ep               # ✅ overrides the theme's shell
    Hero.ep                 # ✅ a component the theme didn't have
  pages/
    index.ep                # ✅ your home page
  # everything else (docs layout, nav, styles…) comes from the theme
```

## Override rules

Resolution order is **site first, then layers in declaration order**:

1. A file in your project always wins over a layer file with the same name.
2. Between layers, the earlier declaration wins.
3. Nothing else changes — a layer page that you have not touched renders exactly
   as it would in the theme's own build.

To keep a theme file but change one detail, override only that file. To go back
to the theme's version, delete your copy.

## Source kinds

`use` entries accept three forms:

| Form | Meaning |
|---|---|
| `pkg:epresso_ui` | An installed Python package that ships `.ep` files |
| `git+https://…/repo@v1` | A git repository, cloned once and cached |
| `path:./vendor/mytheme` | A local directory |

Git sources are cached under `.cache/layers/`. `epresso layers` is the only
command that ships today; the others are planned:

```bash
epresso layers            # shipped — resolved layers and roots
epresso layers update     # planned — re-fetch git layers
epresso use <theme>       # planned — add a theme to [layers] use
```

## Configuration

A layer's `site.toml` is deep-merged **under** your site's, so the theme can ship
defaults for options like `[assets] css` or `[theme]` while you override them:

```toml
# layer's site.toml (theme defaults)
[theme]
accent = "#087a44"
sidebar = true
```

```toml
# your site.toml (override)
[theme]
accent = "#b02a37"
```

Dictionaries merge; lists are replaced wholesale by the higher layer.

> **Scope for v1:** layers do not contribute `content/` or
> `content.config.py`. Your project owns its content and its collections.

## See also

- [Create a theme](guides/themes/create-a-theme.md) — how a theme is structured.
- [Start from a template](guides/themes/from-template.md) — the copy-everything
  alternative.
