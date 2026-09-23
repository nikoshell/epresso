---
title: Markdown
description: How epresso renders Markdown, what is supported, and how links resolve.
order: 20
---

# Markdown

epresso renders Markdown with CommonMark plus tables and strikethrough, so most
GitHub-flavoured documents work unchanged. Front matter is YAML; the body is
Markdown. This fixture is shaped like a real documentation page: an intro, a few
sections with a table and code, and links that need resolution.

## What is supported

CommonMark and the GitHub extensions cover the usual authoring needs.

| Feature | Supported | Notes |
| --- | --- | --- |
| Headings | yes | Slugged and autolinked |
| Tables | yes | `|` syntax |
| Fenced code | yes | Highlighted with Pygments |
| Footnotes | no | Not enabled |
| Wiki links | yes | `[[Page]]` resolves against routes |

Enable more through a plugin when a project needs Pandoc fences or MkDocs
content tabs.

## Links

Relative links to other pages resolve against the route table, so
[the styling guide](/guides/styling/) and [extending epresso](/guides/extending/)
work without knowing the final URL shape. Wiki-style links resolve too:
[[Markdown]] and [[Content collections|Collections]].

## Code

Fenced blocks are highlighted server-side.

```python
import epresso


def build(root: str) -> None:
    site = epresso.Site.load(root)
    result = site.build()
    print(f"built {len(result.pages)} pages")
```

## Front matter

Front matter drives the layout and metadata.

```yaml
title: Markdown
description: How epresso renders Markdown.
order: 20
layout: Base
```

## Summary

That is the surface area. Anything not listed is either a plugin concern or
deliberately left to components.
