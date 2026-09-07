# Configuration

epresso is configured with a TOML file, `site.toml`, validated by Pydantic at load time. Missing file → sensible defaults. Every build/dev/check run loads `site.toml` from the project root.

## Load order

1. `site.toml` — base configuration.
2. `site.<env>.toml` (when `--env <name>` or `EPRESSO_ENV` is set) — **deep-merged** over `site.toml` (per-environment URL, toggles, API keys, …).

See [Environment variables](environment-variables.md for the full environment story.

## Top-level structure

```toml
[site]
name = "My Site"
url = "https://example.com"
language = "en"
description = ""

[build]
output = "dist"        # output dir (default dist)
content = "content"    # collection data dir
pages = "pages"        # routes dir
templates = "templates"
assets = "assets"
static = "public"      # files copied verbatim to the output root
trailing_slash = "always"   # always | never | ignore
clean_urls = true
compress_html = false  # minify HTML (skips <pre>/<script>/<style>)
redirects = true       # emit redirect pages from the `redirects` config

[markdown]
highlight = true       # Pygments syntax highlighting for fenced code
add_slug_ids = true
autolink_headings = true
extensions = []        # extra markdown-it features
components = []        # custom component tags to resolve inside markdown

[assets]
hash = true
css = ["css/main.css"]  # buildable CSS entry points
js  = ["js/app.js"]     # buildable JS entry points

[content]                 # optional draft/private page visibility
show_drafts  = false      #   hide `draft: true` entries in production
show_private = false      #   hide `_`-prefixed (private) entries in production
# Unset (omit) to keep the default: shown in development/preview, hidden in
# production. Set explicitly here and override in site.<env>.toml for dev/prod.

[seo]
sitemap = true
robots = true

[search]
enabled = false
index = "search-index.json"
# When enabled, a core BM-25 search index (no external JS) is written to the
# output at build time. The docs theme consumes it client-side.

plugins = ["mypkg:MyPlugin"]   # dotted-path plugin specs
```

## Redirects

Redirects are configured as `[[redirects]]` tables. Target may be a string
(permanent 301) or `{ destination, status }` for 302:

```toml
[[redirects]]
"/old-home/" = "/"

[[redirects]]
"/legacy/" = { destination = "/new/", status = 302 }
```

Each emits a browser-safe meta-refresh page under `dist/<from>/index.html` and
participates in incremental builds. Set `[build] redirects = false` to disable.
Invalid targets (missing `destination`) are rejected at load time.

## Directory layout

The `build.*` keys let you rename the convention directories. There are helper
accessors on the loaded config: `dir_content()`, `dir_pages()`,
`dir_templates()`, `dir_assets()`, `dir_static()`,
`dir_output()`, and `cache_dir()` (the incremental cache, gitignored).

## Programmatic loading

```python
from epresso.config import load_config

config = load_config(root=".", env="production")
print(config.site.url, config.dir_output())
```

## SEO: canonical URLs

Set the site's absolute origin in `site.toml`:

```toml
[site]
url = "https://example.com"
```

epresso does not auto-emit a canonical tag. Add one in your layout `<head>` so each
page points at its canonical URL (join `site.config.site.url` with the current
path), or rely on your host to serve a canonical link header. `sitemap.xml` and
`robots.txt` are generated from your routes automatically.
