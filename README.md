# epresso

![epresso](https://raw.githubusercontent.com/nikoshell/epresso/main/themes/docs/public/epresso.png)

A modern, **Python-first static site generator** — routes-as-code, content collections, deterministic + incremental builds, and a no-JavaScript-by-default philosophy.

```bash
pip install epresso
epresso new        # interactive: where, and which starter?
cd myblog
epresso dev     # develop with live reload
epresso build   # deterministic, incremental → dist/
```

## Why epresso?

- **Content and routes are separate.** `content/` is data (collections, validated with Pydantic); `pages/` is where routes live as templates that consume the data — a content-first model in Python.
- **Incremental from day one.** A content digest + build graph + reverse index means a content edit re-renders only the affected pages.
- **Deterministic builds.** Same source + config → same output (hashed filenames, stable ordering).
- **JS is optional.** A pure-Python site needs zero Node. esbuild/Tailwind/PostCSS are external binaries used only when you declare JS/CSS.
- **No arbitrary Python in templates.** Templates see a curated set of globals — safe and predictable.

## Features

- Content collections (glob + Python/remote loaders) with **Pydantic schemas**, data collections (JSON/YAML/TOML), content references, drafts & scheduled-content exclusion.
- Routes-as-code: filesystem routing, `{param}` / `{...param}` dynamic routes, `get_static_paths()` sidecars, **`.ep` single-file routes** (Python frontmatter + Jinja), static endpoints (JSON/XML/text), clean URLs, redirects.
- **Jinja2** templates with inheritance, curated globals (`url`, `asset`, `image`, `picture`, `seo`, `get_collection`, `get_entry`, …).
- **`.ep` components** with strict Pydantic `Props` validation, **scoped CSS** (`<style>` blocks, `:global()` opt-out), and **client `<script>` blocks** (bundled page-level JS).
- Dev server (Starlette + watchfiles) with **WebSocket live reload**, sharing the production incremental engine.
- Assets: content-hashed `asset()`, `public/` passthrough, esbuild JS bundling, **PostCSS/Tailwind CSS** pipeline, **Pillow responsive images** (`image()` → WebP srcset).
- **First-class client behavior** — a `.ep` component's `<script>` block is bundled (esbuild) page-level JS, injected before `</body>`. No separate islands/ dir.
- Generated outputs: `sitemap.xml`, `robots.txt`, `llms.txt`, `404.html`, `search-index.json`, and an RSS/Atom helper.
- **Plugin API** — a capability registry: named plugins with lifecycle hooks that receive a scoped `Capabilities` handle (never the raw `Site`), so extensions are deterministic and isolated. See the [plugin guide](https://github.com/nikoshell/epresso/blob/main/docs/guides/extending/plugins.md).
- Theme scaffolding — `epresso new` (interactive), or `epresso new <template|theme|git-url|dir> <dest>`.

## Installation

Requires **Python 3.12+**.

```bash
pip install epresso        # or: uv tool install epresso
```

## Quickstart

```bash
epresso new                 # interactive: dir, then choose a starter
epresso new docs mysite     # or pass the template and destination
cd mysite
epresso dev                 # http://127.0.0.1:4321 with live reload (next free port if busy)
epresso build               # deterministic + incremental build → dist/
epresso preview             # build then serve dist/ (production preview)
epresso check               # validate config + content, list routes
```

The interactive prompt offers:

```
How would you like to start your new project?
  1. A basic, helpful starter project (recommended)
  2. Use the blog template
  3. Use the docs template
  4. Use the minimal (empty) template
```

`epresso new -y` skips the prompts (basic starter, current directory). A blank project:

```bash
epresso init mysite && cd mysite
epresso build
```

## Project layout

```
site.toml            # configuration (TOML)
content.config.py    # define collections + schemas (Pydantic)
content/             # data — collections (markdown / JSON / YAML / TOML)
pages/               # routes (.ep, .md, or .py endpoints)
layouts/             # layout templates (.ep)
components/          # reusable components (.ep), grouped into subdirs
  ui/                #   presentational building blocks
  layout/            #   page/site structure (Header, Nav, Footer, Search)
  sections/          #   visual page regions
  behavior/          #   client-side enhancement / interaction
  features/          #   business-feature components
styles/              # global stylesheets (CSS)
assets/              # buildable assets (images, js); top-level files land at root
public/              # files copied verbatim to the output root
```

> Optional `src/`: when a top-level `src/` directory exists, the source dirs
> above are resolved inside it (Astro/Nuxt-style). `public/`, `dist/`,
> `site.toml` and `content.config.py` stay at the root.

## Configuration (`site.toml`)

### Environments

epresso supports per-environment configuration with a
`.env.development` / `.env.preview` / `.env.production` split:

* `site.<env>.toml` — deep-merged over `site.toml` (per-env URL, toggles, …)
* `.env.<env>` — dotenv-style vars (`EP_SESSIONS_API=...`) exposed to content
  loaders/plugins via `os.environ` and to templates via `env_vars`.

Select with `epresso build --env <name>` (or `EPRESSO_ENV`); `epresso dev` defaults to
`development`, `epresso build`/`preview`/`check` to `production`. In templates,
`{{ env }}` is the active env name and `{{ env_vars.KEY }}` any env var.

```toml
[site]
name = "My Site"
url = "https://example.com"
language = "en"

[build]
output = "dist"
trailing_slash = "always"   # always | never

[assets]
css = ["css/main.css"]      # entry points (esbuild / postcss / tailwind)
js  = ["js/app.js"]

[seo]
sitemap = true
robots = true

[seo.llms]                  # llms.txt (https://llmstxt.org/) for LLM crawlers
enabled = true
path = "/llms.txt"

[search]
enabled = true
index = "search-index.json"

plugins = ["mypkg:MyPlugin"]  # dotted-path plugin specs

[layers]                      # external components/layouts, layered under yours
use = [
  "./vendor/components",
  "pkg:epresso_ui",
  "github:owner/epresso-components@v1",
]
```

## Content collections

Define collections in `content.config.py`:

```python
from pydantic import BaseModel
from epresso.content import define_collection, reference

class Post(BaseModel):
    title: str
    date: str
    tags: list[str] = []
    author: reference("authors")   # content reference
    draft: bool = False

posts = define_collection("posts", glob="*.md", base="./content/posts", schema=Post)
authors = define_collection("authors", loader=fetch_authors)  # remote/derived
```

Fenced code blocks in Markdown are syntax-highlighted with **Pygments** by
default (``markdown.highlight = false`` opts out). Highlighted blocks use
`<code class="language-<lang>">` with token spans; include the generated CSS in
your layout:

```jinja
<style>{{ pygments_css() }}</style>
```

A markdown post with YAML front matter:

```markdown
---
title: Hello
date: 2026-01-01
tags: [python]
---
# Hello

Your **content** here.
```

`get_collection("posts")`, `get_entry("posts", id)`, and `get_entries(...)` resolve data in templates and in `get_static_paths()`. In production builds, `draft: true` and future-dated entries are automatically excluded.

## Routing (routes-as-code)

`content/` is data; `pages/` produces URLs. Three kinds of route:

1. **Direct Markdown page** — `pages/about.md` → `/about/` (layout via front matter).
2. **`.ep` single-file route** — `pages/blog/[slug].ep` with Python frontmatter + Jinja body (recommended):

   ```epresso
   ---
   from epresso.routing import Route

   def get_static_paths():
       return [Route(path=f"/blog/{p.id}/", params={"slug": p.id}, data=p)
               for p in site.get_collection("posts")]
   ---
   <article><h1>{{ props.title }}</h1>{{ content|safe }}</article>
   ```

   The `--- … ---` block is **Python** (run with `site` injected); its variables are
   exposed to the template. `.ep` files compose with components and layout
   components — `{% extends %}`/`{% block %}` are rejected. A static `.ep` route
   needs no `get_static_paths()`.

3. **Static endpoint** — `pages/robots.txt.py` exporting `get()`:

   ```python
   def get():
       return "text/plain", "User-agent: *\nAllow: /\n"
   ```

Pagination is a helper, not magic:

```python
from epresso.routing import paginate

def get_static_paths():
    return paginate(site.get_collection("posts"), per_page=10, base_path="/blog/")
```

### Redirects (Option C)

Redirects are configured in `site.toml` and emitted as routes in the build graph
(so they participate in incremental builds). Targets may be a string (permanent
301) or a `{destination, status}` dict for 302:

```toml
[[redirects]]
"/old-home/" = "/"

[[redirects]]
"/legacy/" = { destination = "/new/", status = 302 }
```

Each emits a browser-safe meta-refresh page under `dist/<from>/index.html`;
`data-epresso-status` reflects the configured HTTP status for edge/host rewrites.
Set `[build] redirects = false` to disable. Invalid targets (missing
`destination`) are rejected at load time.

## The `.ep` file format

`.ep` files unify routes, layouts, and components into a single file:
**Python frontmatter** (`--- … ---`) + **Jinja body**. Content stays in
Markdown; data stays in YAML/JSON/TOML.

### Components with typed props

`components/Card.ep` validates props against a strict Pydantic model
before rendering — no unvalidated kwargs reach the template:

```epresso
---
from pydantic import BaseModel

class Props(BaseModel):
    title: str
    level: int = 3
---
<div class="card"><h{{ props.level }}>{{ props.title }}</h{{ props.level }}>
  {{ content }}</div>
```

Used from any template with the `{% component %}` tag:

```jinja
{% component "Card", title="Hi", level=2 %}Body text{% endcomponent %}
```

### JSX-style component tags

Components can also be written with HTML/JSX-like syntax — epresso rewrites these
to `{% component %}` blocks before parsing, so you don't need the tag at all:

```jinja
<Header />

<main>
  <Hero />
  <FeatureSection layout="three-column" count={items|length} />
  <Card title="Hi">Body <strong>text</strong></Card>
</main>
```

* Only tags that resolve to a registered component are converted — `<main>`,
  `<div>`, `<section>` etc. pass through as plain HTML.
* Attributes are JSX-style: `key="value"` / `key='value'` (string), `key={expr}`
  (expression), or a bare `key` (boolean `true`).
* Paired components take children: `<Card>…</Card>` renders `…` as the
  component's `content`, and children may themselves contain nested components.
* The legacy `{% component %}` tag still works and can be mixed freely.

### Scoped CSS

A `<style>` block in a `.ep` file is extracted, scoped to the component/route's
output (a `data-epresso-<hash>` attribute), and linked from the head:

```epresso
---
---
<style>
  .card { border: 1px solid #ccc; }
  :global(.reset) { margin: 0; }  /* opt out of scoping */
</style>
<div class="card">{{ content }}</div>
```

The scoped CSS is written to `dist/_scoped/epresso-<hash>.css` and a `<link>` is
injected into any page that uses it.

#### Layout components are automatically unscoped

A `.ep` component is **scoped only when it contains a scoped `<style>` block**:
it is then wrapped in a `data-epresso-*` div and its selectors are rewritten. A
component with no scoped CSS — or only `<style is:global>` — renders **unscoped**
(no wrapper). So a layout shell that emits a full `<!doctype html>` document is
automatically unscoped, and any layout `<style>` is made global with
`<style is:global>` or by linking a global stylesheet —
a layout is just a component whose body renders `{{ content }}` (the default
slot):

```epresso
---
---
<!doctype html><html><head><title>{{ title }}</title></head>
<body>{{ content }}</body></html>
```

```jinja
<BaseLayout title={title}>
  <Header />
  <main>…</main>
  <Footer />
</BaseLayout>
```

Layout components may live in `layouts/` (resolved as a component in
addition to `components/`), so `BaseLayout` can stay alongside your
layouts while being composed as a component.

### Slots

Components get a **default slot** (`{{ content }}`, the children between the
open/close tags) plus **named slots** mirroring `<slot name=…>`: a child
`<Fragment slot="name">…</Fragment>` contributes to `slots["name"]` and is
removed from the default `content`.

```jinja
<Card title="Hi">
  <Fragment slot="header">Header content</Fragment>
  Default body content
</Card>
```

```epresso
---
---
<div class="card"><h3>{{ props.title }}</h3><header>{{ slot('header') }}</header>{{ content }}</div>
```

Use `{{ slot('name') or 'fallback' }}` for slot fallback content. Works for any
`.ep` component.

### Client scripts

A `<script>` block in a `.ep` file is extracted, bundled with esbuild (falling
back to a raw module when esbuild isn't installed — JS stays optional), and
loaded on any page that uses the route/component:

```epresso
---
---
<style>.count { color: red; }</style>
<script>
  document.querySelector('.count').addEventListener('click', () => alert('hi'));
</script>
<button class="count">{{ content }}</button>
```

The bundle is written to `dist/_epresso/scripts/<hash>.js` and a
`<script type="module" src="/_epresso/scripts/<hash>.js">` tag is injected before
`</body>` on the pages that use it. Identical script blocks dedupe to one file.

So a single `.ep` file bundles: **Python frontmatter
(template logic) + Jinja body (markup) + `<style>` (scoped CSS) + `<script>`
(page-level client JS)**.

## Templates

Templates are Jinja2 with curated globals and no arbitrary Python. A layout is
an `.ep` component with `<slot/>` (see [Layouts](#layouts)); a Markdown page wraps
itself in one via its front-matter `layout`:

```epresso layouts/Base.ep
---
---
<!doctype html><html><head>
  <title><slot name="title" /></title>
</head><body><slot /></body></html>
```

Globals: `site`, `url()`, `asset()`, `image()`, `seo()`, `get_collection()`, `get_entry()`, `route`, `params`, `props`, `content`.

## Plugins

```python
from epresso.plugins import Plugin

def greeter(*, text="hello"):
    def on_setup(caps):
        caps.add_global("greeting", lambda: text)
    return Plugin(name="greeter", hooks={"on_setup": on_setup})
```

Plugins are **deduplicated by name** and run in **`priority` order**; each hook
receives a narrow `Capabilities` handle rather than the `Site`, and can add
template globals/filters, register content collections & Markdown extensions,
and transform rendered HTML. Enable them from a project `plugins.py` (build with
options via a factory) or `[plugins]` dotted paths in `site.toml`. Lifecycle
hooks: `before_load`, `on_setup`, `after_load`, `before_build`, `after_build`,
`on_assets`. See `examples/plugins/` and the [plugin guide](https://github.com/nikoshell/epresso/blob/main/docs/guides/extending/plugins.md).

## Themes

```bash
epresso new docs mydocs     # docs theme (sidebar nav, ToC-friendly)
epresso new blog myblog     # blog theme (posts, index, RSS feed)
epresso new minimal mysite  # smallest buildable project

# a git source or a local directory, with an optional @ref for a branch/tag
epresso new github:owner/epresso-theme-mytheme mysite
epresso new ./epresso-theme-mytheme mysite
```

Themes are git-cloned (or copied) from their own repos and given to you as a starter project you fully own.

## CLI

| Command | Description |
|---|---|
| `epresso init` | Scaffold a blank project |
| `epresso new [template] [dest]` | Scaffold a project (interactive, or pass a template/theme/git URL/directory) |
| `epresso dev` | Development server with live reload |
| `epresso build` | Deterministic + incremental production build |
| `epresso preview` | Build then serve `dist/` (production preview) |
| `epresso docs` | Build + serve the documentation (port 4321) |
| `epresso clean` | Remove `dist/` and the build cache |
| `epresso layers` | List the component/layout layers resolved from `[layers] use` |
| `epresso check` | Validate config + content, list routes |
| `epresso fmt` | Format `.ep` files to the canonical section structure |
| `epresso lsp` | Run the `.ep` Language Server (diagnostics + formatting) over stdio |
| `epresso version` | Print the version |

## Development

```bash
git clone https://github.com/epresso-ssg/epresso
cd epresso
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run pyright src/epresso
uv run pytest --cov=epresso
```

### Profiling a build

`epresso build` takes profiling flags, and `python -m epresso` is equivalent to
the `epresso` console script so profilers can wrap it directly:

```bash
uv run --project . epresso build themes/docs --perf       # phase timings (render/assets/outputs)
uv run --project . epresso build themes/docs --profile    # cProfile → epresso-profile.pstats
uv run python -m pstats epresso-profile.pstats            # inspect the stats file

# Sampling profiler: ~no interpreter overhead, and it can attach to a running
# dev server, which cProfile cannot.
uv run py-spy record -o perf.svg -- python -m epresso build themes/docs
uv run py-spy top -- python -m epresso dev themes/docs

# Or the interpreter's built-in Linux perf trampoline (no extra deps):
python -X perf -m epresso build themes/docs
sudo perf record -g -o perf.data -- python -X perf -m epresso build themes/docs
```

`cProfile` distorts call-heavy code (the docs theme takes ~2.5 s normally and
~48 s under cProfile), so use it for **call counts and relative ranking**, and a
sampling profiler for wall-clock shares.

### Build-time regression gate

`scripts/bench.py` builds a theme, divides the best run by a fixed CPU
workload measured in the same process, and compares that ratio against
`scripts/perf_baseline.json`. Normalising by the reference workload makes one
baseline portable between a laptop and a CI runner. CI runs it on every PR and
fails on a slowdown past the threshold (25%, or `$EPRESSO_PERF_THRESHOLD`).

```bash
uv run python scripts/bench.py                  # gate against the baseline
uv run python scripts/bench.py --update         # re-record after an intended change
uv run python scripts/bench.py --runs 5 --theme themes/blog
```

Exit codes: `0` within threshold, `1` regression, `2` the build itself failed or
produced no pages. The baseline is pinned to the interpreter it was recorded on;
recording it under a different Python makes the gate report-only until you
re-record. A change of CI hardware may need one `--update` run.

### Run the bundled themes

The repo ships runnable theme projects under `themes/` (`basic`, `blog`,
`docs`, `website`). From the repo root, point any epresso command at one with
`--project .`:

```bash
uv run --project . epresso dev themes/basic      # dev server with live reload
uv run --project . epresso build themes/basic    # build → themes/basic/dist
uv run --project . epresso check themes/basic    # validate config + content
uv run --project . epresso preview themes/basic  # build + serve dist/
```

The `website` example is the most feature-rich — it exercises `.ep` components
and scoped CSS.

## Editor support

Neovim / Vim syntax highlighting for `.ep` files (Python frontmatter +
Jinja2 body) ships in `extras/nvim/`. Add it to your runtimepath once and every
epresso project is highlighted automatically:

```lua
-- ~/.config/nvim/init.lua
vim.opt.rtp:append("/path/to/epresso/extras/nvim")
```

See [`extras/nvim/README.md`](https://github.com/nikoshell/epresso/blob/main/extras/nvim/README.md) for details and LazyVim
instructions.

For **VS Code**, `extras/vscode/` bundles syntax highlighting, live diagnostics
(from the bundled `epresso lsp`) and formatting (via `epresso fmt --stdin`):
open `extras/vscode/` and press `F5`, or package it with
`npx @vscode/vsce package`. `epresso lsp` is a dependency-free Language Server
that any LSP-capable editor can drive (see
[docs/editor-setup](docs/editor-setup/index.md)). The TextMate grammar is standard
JSON, so other `.tmLanguage.json` editors can reuse it. See
[`extras/vscode/README.md`](https://github.com/nikoshell/epresso/blob/main/extras/vscode/README.md).

## License

MIT
