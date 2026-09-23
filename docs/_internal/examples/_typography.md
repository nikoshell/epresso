---
title: Typography & Markdown showcase
description: A private page exercising epresso's Markdown and typography output (headings, code, tables, quotes, lists).
---

# Typography & Markdown showcase

A private page (note the `_` prefix) used to review how Markdown renders. It is
hidden from production and visible only in `development`/`preview`.

## Headings

Markdown headings map to `h2`–`h6` here (the document `h1` becomes the page
title). Anchors are added automatically — hover a heading to copy its link.

### Third level

#### Fourth level

## Inline styles

- **Bold**, *italic*, and `inline code`.
- A [link to the markdown guide](guides/content/markdown.md) and an external
  link to [markdown-it](https://github.com/markdown-it/markdown-it).

## Code

Fenced code is syntax-highlighted and gets a copy control:

```python
def greeting(name: str) -> str:
    """A tiny function to show off code blocks."""
    return f"Hello, {name}!"
```

## Blockquote

> epresso renders **plain HTML by default**. Nothing ships client-side
> JavaScript unless you add it.

## Lists

Ordered and unordered lists, plus a task list:

1. Content collections are data.
2. Pages are routes.
3. Builds are deterministic and incremental.

- No-JavaScript by default
- Scoped CSS
- Live-reload dev server

## Table

| Feature | Default |
|---------|---------|
| Markdown | `commonmark` + tables + strikethrough |
| CSS | plain, via `asset()` |
| JS | none unless you add it |

## Horizontal rule

---

This page exercises the styling you see across the docs theme.
