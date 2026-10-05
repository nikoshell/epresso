# Changelog

## 0.7.0

### Added
- **MkDocs migration**: `epresso docs .` reads `mkdocs.yml` live; `epresso import mkdocs`
  writes a `docs.toml` (nav, redirects, extra CSS/JS, blog options; unsupported keys warn).
- **`epresso_mkdocs`** plugin: admonitions, collapsible blocks, content tabs, nested fences,
  attr_list, md_in_html, snippets, definition lists, footnotes, abbreviations, task lists,
  mark/ins/sub/sup, keys. `epresso_mkdocs_tabs` is now an alias.
- **`epresso_blog`** plugin: posts, paginated index, yearly archive, categories, authors,
  RSS, MkDocs-compatible URLs; "Blog" section in the docs sidebar.
- **`epresso_social`** plugin: `og:image` social cards per section, page or collection.
- **`epresso_optimize`** plugin: responsive WebP `srcset`, lazy loading and intrinsic size
  for content images.
- `docs.toml`: per-source `nav`, `redirects`, `extra_css`, `extra_javascript`, `[blog]`;
  unknown keys are an error.
- Zero-config `epresso docs <dir>`: `README.md` homepage + `docs/` pages, placeholder
  homepage when `README.md` is missing.
- **Parallel rendering** across CPU cores (`[build] jobs`, `EPRESSO_JOBS`).
- `site.get_collection_index()` for nav/listings that don't depend on page bodies.
- `EPRESSO_DISABLE_PLUGINS=a,b`; plugin capabilities `add_markdown_it_plugin`,
  `add_static(exclude=...)`; `transform_html` ctx gets `data`.

### Changed
- Plain `epresso docs` always shows epresso's own documentation; use `epresso docs .` for
  the current project.
- Only docs-source files a built page references are published.
- Raw-HTML relative URLs resolve against the page URL, Markdown URLs against the source
  file; relative links to files (pdf, zip, …) are rewritten too.
- HTML-transform plugins no longer disable incremental page reuse.
- Much faster cold and warm builds (1,000 pages: ~22s → ~9s cold, ~23s → ~5s warm).

### Fixed
- Page cache now invalidates when epresso itself changes.
- Reused pages were missing from the search index.
- Blog post images were published twice.

## 0.6.1

### Fixed
- A `README.md` next to a placeholder `index.md` (e.g. pwndbg's docs) now makes one
  landing page instead of a sidebar "Overview" entry that 404'd.
- `epresso docs` no longer copies epresso.top's own `[[redirects]]` into other
  projects' docs.

## 0.6.0

### Added
- **`epresso_docs` plugin** (bundled): one `docs` collection from several Markdown
  sources — local dirs, `github:owner/repo[@ref]`, git URLs — with per-source
  `dir`, `prefix`, `title`, `repo_url`. One sidebar, search index and prev/next
  chain; duplicate pages are a build error; per-page "view source" links.
- `[plugin.epresso_docs] base = "/docs/"` puts docs under a path inside any site,
  leaving the host's pages, layouts and CSS alone.
- **`docs.toml`** for `epresso docs`: sources, `title`, `[site]`, `[theme]` options.
  With no argument, `epresso docs` uses `./site.toml`, else `./docs.toml` / `./docs/`.
- Plugin options: `[plugin.<name>]` tables read via `caps.options`.
- Plugin capabilities `add_layer`, `add_route`, `add_static` (in `before_load`).
- Layers now contribute `styles/`, `assets/` and `public/` (the site wins clashes).
- Relative images in docs sources are published and resolve.
- Docs theme branding: `logo.svg` / `favicon.ico` / `og-image.png` next to the
  docs, or `[theme] logo` / `favicon` / `og_image`.

### Changed
- **Breaking:** `[docs]` / `[[docs]]` sections are removed (a leftover one is a
  config error) — use `[plugin.epresso_docs] base`.
- **Breaking:** docs theme components and layouts are prefixed `Docs*`
  (`DocsBase`, `DocsPage`, `DocsHighlight`, …); its stylesheet is `styles/docs.css`;
  its fonts live under `/docs-theme/fonts/`; it no longer has a `content.config.py`.
- The docs theme is brand-neutral: no epresso logo/favicon by default; the header
  shows the site name; the green dot is opt-in (`[theme] brand_dot`).
- `epresso docs <dir|git>` names the site after the source instead of "epresso".
- The "Built with epresso" footer link goes to epresso.top, with UTM tags.
