---
title: Draft example
description: A page marked draft, so it is hidden from production builds and only shown in development/preview.
draft: true
---

# Draft example

This page is a **draft**. In a production build it is excluded (see
[draft visibility](guides/build/environment-variables.md)); in `development`
and `preview`
environments it stays visible so you can review it before publishing.

## Why drafts

Draft/private visibility is controlled per environment in `site.toml`:

```toml
[content]
show_drafts  = false   # hide drafts in production (default)
show_private = false
```

Flip them in `site.<env>.toml` to preview drafts while developing.
