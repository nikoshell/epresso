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

## Layout

```
site.toml            # config: [theme], [build] component/layout roots
content.config.py    # defines the docs collection (schema + loader)
pages/
  [...slug].ep       # one dynamic route → a page per doc
  404.ep
components/          # UI components + layouts (each owns scoped <style>/<script>)
  primitives/  controls/  patterns/  navigation/  structure/  layouts/
styles/global.css    # design tokens, fonts, and page base
```

## What's where

- `components/layouts/Base.ep` — the document shell (`<html>`, head, header, footer)
- `components/layouts/Doc.ep` — the docs page (sidebar + content + ToC rail)
- `components/navigation/` — `Nav` (sidebar), `Breadcrumbs`, `Toc`
- `components/patterns/` — `Markdown` (prose), `Highlight` (code blocks), `CodeHead`, `SearchOverlay`, `ImageLightbox`
- `components/controls/` — `ThemeToggle`, `SearchButton`, `PageActions`, `Pager`

## Deploying to GitHub Pages

A ready-made workflow is included in the repo (`.github/workflows/deploy-docs.yml`):
on every push to `main` it builds the docs site and deploys `dist/` to GitHub
Pages. The theme emits root-relative URLs, which work on a User/Organization
Pages site or a custom domain; on a project Pages site you'll need a custom
domain or `[theme] docs_base` set.

## License

MIT
