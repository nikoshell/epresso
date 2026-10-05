---
order: 365
description: Build an MkDocs / Material for MkDocs project with epresso — live from mkdocs.yml, or imported once into docs.toml.
---

# Migrate from MkDocs

epresso builds an existing MkDocs (or Material for MkDocs) project with no
content changes. You can try it straight from your `mkdocs.yml`, then switch to
a `docs.toml` when you are ready.

## Try it

Run `epresso docs .` in the directory that holds `mkdocs.yml`:

```bash
cd my-mkdocs-project
epresso docs .               # serve on :4321
epresso docs . --out site/   # or write a static build
```

epresso reads `mkdocs.yml` live and renders `docs_dir` with the docs theme.
Settings it can't map are printed as warnings; nothing is written.

## Switch over

```bash
epresso import mkdocs        # mkdocs.yml → docs.toml
epresso docs .
```

`epresso import mkdocs` writes the same settings into a `docs.toml`. From then on
`epresso docs .` uses `docs.toml` (it tells you it is ignoring `mkdocs.yml`). It
won't overwrite an existing `docs.toml` unless you pass `--force`. Pass
`--theme ../my-theme` to record your own theme.

## What carries over

| `mkdocs.yml` | epresso |
|---|---|
| `site_name` | `title` |
| `site_url`, `site_description` | `[site] url`, `description` |
| `repo_url`, `edit_uri` | the page source links |
| `docs_dir` | the docs source |
| `nav` | the sidebar (`nav` on the source); pages not in `nav` are built but not listed |
| `extra_css`, `extra_javascript` | loaded after the theme's CSS |
| `redirects` plugin `redirect_maps` | `[[redirects]]` |
| `search`, `minify` plugins | built in |
| `social` plugin | [`epresso_social`](/guides/styling/social-cards/) (on in the docs theme) |
| `blog` plugin | [`epresso_blog`](/guides/content/blog/) (on in the docs theme), same URLs |
| `optimize` plugin | [`epresso_optimize`](/guides/styling/images/) (on in the docs theme) |
| `theme` | ignored — the look comes from the docs theme or `--theme` |

## Markdown syntax

The docs theme enables the `epresso_mkdocs` plugin. Any other site can turn it
on with `plugins = ["epresso_mkdocs"]` in `site.toml`. It renders:

- admonitions (`!!! note "Title"`) and collapsible blocks (`???`, `???+`)
- content tabs (`=== "Label"`), also inside admonitions and list items
- fenced code nested in admonitions, tabs and lists
- `attr_list` (`## Title { #id .class }`, `Paragraph {: .lead }`, `[link](x){ .button }`)
  and `md_in_html` (`<div markdown>`)
- snippets (`--8<-- "path/file.md"`), resolved against the project directory;
  a path outside the project is an error
- definition lists, footnotes, abbreviations (`*[HTML]: …`), task lists,
  `==mark==`, `^^insert^^`, `^sup^`, `~sub~` and `++ctrl+alt+del++` keys

The HTML uses Material's class names (`.admonition`, `.admonition-title`,
`details.tip`, `.tabbed-set`, `.keys`), so `extra_css` written for Material keeps
working.

!!! note "Limits"
    Markdown inside `<div markdown>` must be separated from the tags by blank
    lines. Icons and emoji (`:material-…:`), math (`arithmatex`) and Mermaid
    diagrams are not supported yet; `epresso` names any unsupported extension.

## Plugins without an equivalent yet

`mkdocstrings` and `macros` are reported as
warnings and skipped. The rest of the site still builds.
