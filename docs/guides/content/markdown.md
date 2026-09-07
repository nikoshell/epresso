# Markdown

epresso renders Markdown with **markdown-it-py** (`commonmark` preset with tables,
strikethrough, linkify, and typographer enabled). The output is
`RenderedContent` with `html` plus metadata (headings, image paths).

## Front matter

A markdown entry with YAML front matter:

```markdown
---
title: Hello
date: 2026-01-01
tags: [python]
---
# Hello

Your **content** here.
```

Front-matter fields become the entry's validated `data`. A direct Markdown page
uses front matter for its `layout` and `title`; the `content` block of the layout
is filled with the rendered HTML.

## Configuration

```toml
[markdown]
highlight = true        # Pygments syntax highlighting for fenced code
add_slug_ids = true     # add id attributes to headings
autolink_headings = true
toc_heading = null      # optional heading used for a table of contents
extensions = []         # extra markdown-it features
components = []         # custom component tags to resolve inside markdown
```

## Syntax highlighting

Fenced code blocks are highlighted with **Pygments** by default
(`highlight = false` opts out). Highlighted blocks use
`<code class="language-<lang>">` with token spans. Include the generated CSS in
your layout:

```jinja
<style>{{ pygments_css() }}</style>
```

## Heading anchors

Headings get `id="<slug>"` attributes (from `add_slug_ids`, on by default), and
when `autolink_headings` is enabled (default) each heading carries a GitHub-style
`#` anchor link (shown on hover) linking back to itself:

```html
<h2 id="load-order"><a class="heading-anchor" href="#load-order" aria-hidden="true">#</a>Load order</h2>
```

## Headings & images metadata

`_extract_headings_and_images` runs an AST pass over the parsed tokens, producing
`headings` (`[{depth, slug, text}]`) and `image_paths` for each entry — useful
for building a table of contents or an image list:

```python
entry.headings   # -> [{depth, slug, text}, ...]
```

## Link resolution

epresso resolves GitHub/wiki-style links to site URLs. A target maps to a page by
its content id, slug, or title (case-insensitive). Absolute paths, external URLs,
and `#anchors` pass through unchanged.

| Syntax | Example | Renders to |
|--------|---------|------------|
| `[Label](Page.md)` | `[Layouts](../../basics/layouts.md` | `→ /basics/layouts/` |
| `[Label](Page)` | `[Config](../build/configuration.md` | `→ /guides/configuration/` |
| `[Label](/path)` | `[CLI](/docs/cli/)` | `→ /develop-and-build/cli/` (as-is) |
| `[[Page]]` | `[[Routing]]` | `→ /guides/routing/` |
| `[[Page\|Label]]` | `[[Routing\|routing guide]]` | `→ /guides/routing/` as "routing guide" |
| `[wiki_page:Page]` | `[wiki_page:Layouts]` | `→ /basics/layouts/` |

Unresolvable targets (no matching page) are left exactly as written.

## Components in markdown

Allow-listed component tags work directly in Markdown, mirroring MDX's
`components` map. Tags listed in `[markdown] components` are captured at token
level (children stay real Markdown tokens) and expanded to epresso component
output at template time via `expand_md_components`:

```toml
[markdown]
components = ["Button", "YouTube"]
```

```markdown
<Button url="https://example.com">Read more</Button>

<YouTube id="abc123" />
```

Children remain Markdown tokens, so `**bold**` etc. work inside a component.
`md/` wrapper components (e.g. `components/md/YouTube.ep`) take
precedence over the general basename search. Page front matter is exposed to
markdown components via `{{ md_page_data() }}`.

## Rendering markdown programmatically

The `render_md()` global renders a Markdown string to safe HTML inside a
component or template (handy for prose stored in front matter):

```jinja
{{ render_md(card_body) | safe }}
```

Relative image `src` in rendered markdown is rewritten against the page base.
