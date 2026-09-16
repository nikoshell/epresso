---
title: Build with components only
order: 20
draft: true
description: Take a component library and a token stylesheet, and keep your own layout and pages.
---

> **Partly available.** Component layers work today — see
> [Layers](guides/extending/layers.md). A library's component files layer in;
> its `styles/`/`assets/` do not (v1), so copy its prebuilt CSS into your own
> `styles/`, or ship it in a `<style is:global>` component.

A component library gives you building blocks, not a site. You keep your own
layout shell and pages and drop the library underneath.

## The stack

```toml
# site.toml
[layers]
use = [
  "pkg:epresso_ui",          # styled components + tokens (depends on the below)
  "pkg:epresso_components",  # unstyled behaviour + markup
]
```

- `epresso-components` — markup, accessibility and behaviour, structural CSS
  only.
- `epresso-ui` — design tokens plus styled overrides of the same components.
- Later entries win less: `epresso_ui` is declared first, so `<Button>` resolves
  to the styled version. Drop `epresso_ui` and the same tag renders the unstyled
  component.

## You still own the shell and the routes

```tree
mysite/
  site.toml
  layouts/Base.ep        # your HTML shell
  components/
  pages/
    index.ep             # your routes
    about.ep
  styles/
    global.css           # your tokens / overrides
```

```epresso
---
---
<!doctype html>
<html lang="{{ site.config.site.language }}">
  <head>
    <meta charset="utf-8">
    <title>{{ props.title }}</title>
    <link rel="stylesheet" href="{{ asset('global.css') }}">
  </head>
  <body>
    <main><slot/></main>
  </body>
</html>
```

```epresso
---
---
<Base title="Home">
  <Button variant="primary">Get started</Button>
  <Badge tone="success">New</Badge>
</Base>
```

`Button` and `Badge` come from the library. Their scoped CSS is written to
`dist/_scoped/` and linked only into pages that use them — no extra wiring.

## Styling the library

`epresso-ui` ships a **prebuilt** stylesheet for its prebuilt utility classes.
Because v1 layers do not contribute `styles/`, that stylesheet is not resolved
by `asset()` — either copy it into your own `styles/` and link it as usual, or
have the library ship the CSS in a `<style is:global>` block inside one of its
components (which works today). Then override its tokens with your own global
CSS:

```epresso
<link rel="stylesheet" href="{{ asset('global.css') }}">
```

```css
/* styles/global.css */
:root {
  --accent: #b02a37;   /* overrides the library's default token */
}
```

> **Note:** utility-class libraries must ship **prebuilt CSS**. A consumer's
> `uno.config.ts` / `tailwind.config.*` only scans the *site's* files, so
> utilities used inside an installed package would never be generated. A library
> that bakes class strings into components must therefore ship the compiled
> stylesheet, not rely on the consumer's build tool.

## Mixing in your own components

Your components always win over library components with the same name — you can
wrap a library component and restyle it without forking:

```epresso
---
from pydantic import BaseModel

class Props(BaseModel):
    label: str
---
<Button variant="primary" class_name="brand-cta">{{ props.label }}</Button>
```

## See also

- [Components](../basics/components.md) — the `.ep` format, props and scoped CSS.
- [Styling and CSS](../guides/styling/styling.md) — assets, tokens and
  PostCSS/Tailwind.
- [Use a theme as a layer](guides/themes/planned/use-a-theme.md) — the same
  mechanism, for whole themes.
