---
order: 332
---

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
repository = ""        # source repo URL for "view source / edit this page" links
                       # (unset → derived from the git origin remote)
branch = "main"        # branch those source/edit links point at
                       # (unset → the repo's HEAD branch)
docs_source = ""       # set when previewing docs from a path (`epresso docs --theme`)

[build]
output = "dist"        # output dir (default dist)
content = "content"    # collection data dir
pages = "pages"        # routes dir
layouts = "layouts"    # default layout dir
components = "components"
styles = "styles"      # global stylesheet dir
assets = "assets"
static = "public"      # files copied verbatim to the output root
trailing_slash = "always"   # always | never | ignore
clean_urls = true
compress_html = false  # minify HTML (skips <pre>/<script>/<style>)
redirects = true       # emit redirect pages from the `redirects` config

[markdown]
backend = "native"      # renderer: "native" (Python); "rust" = optional accelerator
highlight = true       # Pygments syntax highlighting for fenced code
add_slug_ids = true
autolink_headings = true
toc_heading = ""       # reserved: declared but not implemented — nothing reads it yet
default_layout = ""    # layout for direct Markdown pages that set none of their own
code_component = ""    # component to render fenced code blocks through, server-side
code_components = {}   # per-language overrides, e.g. { tree = "Tree" }
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

[seo.llms]              # llms.txt (https://llmstxt.org/)
enabled = true
path = "/llms.txt"
title = ""             # defaults to the site name
description = ""       # defaults to the site description

[seo.rss]              # RSS/Atom feed
enabled = false
collection = ""        # content collection to build the feed from
path = "/rss.xml"
title = ""             # defaults to the site name
description = ""       # defaults to the site description
limit = 0              # 0 = all entries
url_template = "/{collection}/{id}/"   # URL for each item

[search]
enabled = false
index = "search-index.json"
# When enabled, a core BM-25 search index (no external JS) is written to the
# output at build time. The docs theme consumes it client-side.

[dev]
toolbar = { enabled = true, placement = "bottom" }   # dev-only overlay; placement: bottom | top

[[docs]]                # build a docs section into the site (repeat for several)
source = "docs"         # Markdown dir, or a project dir with its own site.toml
base = "/docs/"         # public sub-path within the site
theme = ""              # theme for bare Markdown (default: the bundled docs theme)
out = ""                # output subdir of dist/ (default: derived from base)

plugins = ["mypkg:MyPlugin"]   # dotted-path plugin specs

[layers]
use = [                          # extra component/layout roots, layered under the site's own
  "./vendor/components",         #   a directory path
  "pkg:epresso_ui",              #   an installed Python package
  "github:owner/epresso-components@v1",  # a repo (tarball, cached in .cache/layers/)
]
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
`dir_layouts()`, `dir_components()`, `dir_styles()`,
`dir_assets()`, `dir_static()`,
`dir_output()`, and `cache_dir()` (the incremental cache, gitignored).

All of these are resolved against the project root, as are `site.toml` and
`content.config.py`. Content collection `base` paths are resolved against the
same root. See
[Project structure](../basics/project-structure.md).

External component/layout roots come from `[layers] use` — see
[Layers](guides/extending/layers.md).

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
