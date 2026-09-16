# epresso-theme-docs

A **single-repo documentation theme** for [epresso](https://github.com/nikoshell/epresso).
It renders one repository's Markdown docs into a navigable docs site with a
**sidebar**, **on-page table of contents**, and a **prev/next pager**.

Only `README.md` / `index.md` files become hubs (a directory's or the repo root's
landing) — no overviews are auto-generated.

## Usage

Preview a repo's docs:

```bash
uv run --project . epresso docs --theme themes/docs <path/to/repo>
```

Build or serve this repo's own docs (the project's `docs/`):

```bash
uv run --project . epresso build themes/docs
uv run --project . epresso dev themes/docs
```

## Configuration

All theme options live in `[theme]` in `site.toml`. Each is overridable with an
`EPRESSO_<NAME>` env var:

| Option      | Env var             | Default | Meaning                                        |
|-------------|---------------------|---------|------------------------------------------------|
| `repo_name` | `EPRESSO_REPO_NAME`  | `""`    | URL prefix + sidebar/breadcrumb root (empty = served from the root) |
| `docs_dir`  | `EPRESSO_DOCS_DIR`   | `docs`  | which subdir of the source repo holds the docs (e.g. `docs`, `_posts`) |
| `docs_base` | `EPRESSO_DOCS_BASE`  | `""`    | extra URL prefix (e.g. `/docs/` on GitHub Pages) |
| `page_actions` | — | `true` | copy-page button + markdown menu, and the per-page `<page>.md` routes they use (set `false` to drop both) |

### Footer

The footer is an auto-fit grid — **optional menu**, **optional build info** —
above the credit line. Both columns are off by default:

```toml
[theme.footer]
# links; absolute (http…) hrefs are used as-is, everything else goes through
# the build base
menu = [
  { label = "Documentation", href = "/" },
  { label = "GitHub", href = "https://github.com/nikoshell/epresso" },
]
# build provenance. `true` shows env + the epresso version; a table adds rows
# (e.g. { commit = "abc1234" })
debug = true
```

Columns wrap with `auto-fit` (`minmax(13rem, 1fr)`), so a footer with one or two
columns — or a narrow viewport — leaves no empty gap.

## Keyboard shortcuts

Keys are bare (no `Ctrl`/`⌘`) and are ignored while you're typing in a field.
The list is available in-page with `?`:

| keys | action |
|------|--------|
| `Ctrl`/`⌘`+`K` | open search |
| `?` | keyboard shortcuts |
| `[` / `]` | previous / next doc (no-op when the pager has no such link) |
| `<` / `>` (`,` `.`) | previous / next section (ToC heading) |

In the dev server the toolbar adds `Shift`+`Alt`+`D` (show/hide the toolbar) and
`Shift`+`Alt`+`I` (inspect elements).

## Page actions & per-page markdown

On by default — `[theme] page_actions = false` turns it off, which also drops
the `.md` routes. Every doc page ships its markdown next to the HTML, at `<page>.md` (e.g.
`/basics/routing.md`) — the page's `.ep` route returns it from
`get_static_paths()`, and routes carrying their own `body` are written verbatim.
The `PageActions` control above the article uses it:

- **Copy page** copies that markdown (the article's rendered text is the
  fallback if the fetch fails).
- **More options** — a native `<details>`, so the links work without JS — has
  entries each labelled with a subtitle: *Copy page* (copy this page as
  Markdown), *View as Markdown* (open this page as plain Markdown, new tab),
  *View source of this page* (the source path, when `[site] repository` is set),
  and *Open in ChatGPT* / *Open in Claude* (ask questions about this page). The
  AI links pass the absolute `.md` URL, built from `[site] url` + the page path.

The `.md` files are excluded from the sitemap, `llms.txt` and the search index
(they aren't HTML pages) and count as endpoints in the build summary.

## Layout

```
site.toml            # config: [theme], [build] component/layout roots
content.config.py    # defines the docs collection (schema + loader)
pages/
  [...slug].ep       # one dynamic route → a page per doc
  404.ep
layouts/             # document shells (Base, Doc)
components/          # UI components (each owns scoped <style>/<script>)
  primitives/  controls/  patterns/  navigation/  structure/
styles/global.css    # design tokens, fonts, and page base
public/              # fonts, images, favicon, toolbar assets
```

## What's where

- `layouts/Base.ep` — the document shell (`<html>`, head, header, footer)
- `layouts/Doc.ep` — the docs page (sidebar + content + ToC rail)
- `components/navigation/` — `Nav` (sidebar), `Breadcrumbs`, `Toc`
- `components/patterns/` — `Markdown` (prose), `Highlight` (code blocks), `CodeHead`, `SearchOverlay`, `ShortcutsOverlay`, `ImageLightbox`
- `components/controls/` — `SearchButton`, `PageActions`, `Pager`

## Deploying to GitHub Pages

A ready-made workflow is included in the repo (`.github/workflows/deploy-docs.yml`):
on every push to `main` it builds the docs site and deploys `dist/` to GitHub
Pages. The theme emits root-relative URLs, which work on a User/Organization
Pages site or a custom domain; on a project Pages site you'll need a custom
domain or `[theme] docs_base` set.

## License

MIT
