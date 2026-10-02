# Changelog

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
