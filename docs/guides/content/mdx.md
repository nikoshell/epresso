---
order: 312
---

# MDX

epresso does not support MDX. Markdown is rendered with markdown-it
([Markdown](markdown.md).

You can still mix interactive/output components into Markdown using **component
tags in content** — the theme registers components (e.g. `Highlight`) that the
Markdown renderer resolves server-side. So most MDX patterns (components inside
a document) have a direct equivalent without a JSX/MDX compiler. Author the rest
as plain Markdown with front matter.
