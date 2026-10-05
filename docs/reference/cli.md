---
order: 420
---

# CLI

epresso ships a single `epresso` command with subcommands. Most commands take an
optional project directory (`root`), defaulting to the current directory.

| Command | Description |
|---------|-------------|
| `epresso init [root]` | Scaffold a blank project |
| `epresso new [template] [dest]` | Scaffold a project (interactive, or pass a template/theme/git URL/directory) |
| `epresso dev [root]` | Development server with live reload |
| `epresso build [root]` | Deterministic + incremental production build |
| `epresso preview [root]` | Build then serve `dist/` (production preview) |
| `epresso docs [root]` | Build + serve docs (port 4321) or write them with `--out`; no `root` = epresso's own docs, `.` = this project |
| `epresso import mkdocs` | Write a `docs.toml` from an MkDocs `mkdocs.yml` |
| `epresso serve [root]` | Serve an already-built `dist/` (no build) |
| `epresso clean [root]` | Remove `dist/` and the build cache |
| `epresso layers [root]` | List the component/layout layers resolved from `[layers] use` |
| `epresso check [root]` | Validate config + content, list routes |
| `epresso fmt [paths…]` | Format `.ep` files to the canonical section structure |
| `epresso lsp` | Run the `.ep` Language Server (diagnostics + formatting) over stdio |
| `epresso inspect [root]` | Inspect the build graph (routes + content → route edges) |
| `epresso deploy [root]` | Build and deploy (GitHub Pages by default) |
| `epresso version` | Print the version |

## `epresso docs`

Build a directory of Markdown as a documentation site and serve it (default port
4321), or write a static build with `--out`.

```bash
epresso docs                                 # epresso's own documentation
epresso docs .                               # this project (site.toml / docs.toml / mkdocs.yml / zero-config)
epresso docs ../my-repo                      # a local checkout
epresso docs github:owner/repo@v1            # clone + render a remote repo
epresso docs https://github.com/owner/repo   # same, by URL
epresso docs ../my-repo --theme ../my-theme  # with a custom theme
epresso docs ../my-repo --out dist/docs      # static build, no server
```

`root` is a **git source** or a directory:

- **git source** — `github:owner/repo[@ref]`, `git+https://…`, or a plain
  `https://` / `git@` URL. It is shallow-cloned into `.cache/repos/` (reused on
  later runs; delete that directory to re-fetch a moved ref) and rendered. The
  clone keeps its `.git`, so the repository links below resolve to that repo.
- **project** — a directory with a `site.toml`, built as-is.
- **`docs.toml`** — a directory with a `docs.toml` (and no `site.toml`): the
  docs theme with the `epresso_docs` plugin, fed by the sources it lists (see
  below).
- **any other directory (zero-config)** — the top-level `README.md` is the
  homepage and every Markdown file under `docs/` is a page (override the dir with
  `EPRESSO_DOCS_DIR` or `REPO_DOCS`). No `docs/` → a console warning and a site
  with just the homepage. No `README.md` → a placeholder homepage explaining what
  to create (also in `--out` builds). `README.md` wins over `docs/index.md`.
  Other files in the directory are not read.

- **`mkdocs.yml`** — an MkDocs project (no `site.toml` or `docs.toml`): read
  live and rendered with the docs theme. See
  [Migrate from MkDocs](/guides/themes/migrate-from-mkdocs/).

With no argument, `epresso docs` shows epresso's own documentation; when the
current directory holds a `site.toml`, `docs.toml` or `mkdocs.yml` it also prints
a hint to run `epresso docs .`. For a directory it checks, in order: `site.toml`,
`docs.toml`, `mkdocs.yml`, then zero-config. With both `docs.toml` and
`mkdocs.yml` it uses `docs.toml` and says so.

### Several sources: `docs.toml`

```toml
title = "My Project"            # → [site] name
extra_css = ["css/extra.css"]   # copied, loaded after the theme CSS
extra_javascript = ["js/extra.js"]
redirects = [{ "/old/" = "/guide/install/" }]

[[sources]]
source = "docs"                 # local dir, relative to docs.toml
# optional, MkDocs-shaped: replaces folder grouping for this source;
# unlisted pages are built but not shown in the sidebar
nav = ["index.md", { "Guide" = ["guide/install.md", { "Usage" = "guide/usage.md" }] }]

[[sources]]
source = "github:org/plugin-a@v1"
dir = "docs"                    # dir inside the source (default "docs" for git, "." local)
prefix = "/plugins/a/"          # URL prefix (default "/")
title = "Plugin A"              # sidebar group label

[site]                          # optional overrides for the generated site.toml
url = "https://docs.example.com/"

[theme]                         # optional theme options (or `theme = "path"` for another theme)
logo = "logo.svg"
```

Every source merges into one docs collection — one sidebar, one search index,
one prev/next chain. Two sources producing the same page are a build error;
give one a `prefix`. `docs.toml` is a shorthand: epresso compiles it into a
`site.toml` with `plugins = ["epresso_docs"]` and a `[plugin.epresso_docs]`
table, which is exactly what a full site would write. Without `sources` it
reads `./docs`. Relative images in every source resolve (see the plugins guide); only files a built page references are published.
Allowed top-level keys: `title`, `theme`, `site`, `sources`, `base`, `redirects`,
`extra_css`, `extra_javascript`, `blog` (options for [`epresso_blog`](/guides/content/blog/)); per source: `source`, `dir`, `prefix`, `title`,
`repo_url`, `nav`. Anything else is an error.

### The link back to the repository

When the source is a git checkout, epresso also points the generated pages at
that repository. It reads the checkout's `origin` remote and default branch and
writes them into the generated `site.toml`:

```toml
[site]
repository = "https://github.com/you/my-repo"
branch = "main"
```

Those two fields drive the **view / edit this source** links on every page, so
the preview links to the real repository instead of the theme's own. The source
path itself is recorded as `docs_source`, and the collection it populates as
`[theme] docs_base`. See [Preview a repository's docs](/guides/themes/preview-repo-docs/)
for the full workflow.

| Flag | Meaning |
|------|---------|
| `--theme PATH` | Theme project used for bare Markdown (default: the bundled docs theme) |
| `--out DIR` | Write a static production build to `DIR` instead of serving |
| `--port N` | Port to serve on (default 4321; the next free port is used if busy) |
| `--host H` | Host to bind (default `127.0.0.1`) |
| `--env NAME` | Environment (loads `site.<env>.toml` + `.env.<env>`; default `production`) |
| `--perf` | Print detailed build-phase timings |

## `epresso import mkdocs`

Write a `docs.toml` from an MkDocs `mkdocs.yml`, then preview with `epresso docs .`.

```bash
epresso import mkdocs                    # ./mkdocs.yml → ./docs.toml
epresso import mkdocs site/mkdocs.yml --theme ../my-theme
epresso import mkdocs --force            # overwrite an existing docs.toml
```

Settings without an epresso equivalent are listed as warnings. See
[Migrate from MkDocs](/guides/themes/migrate-from-mkdocs/).

| Flag | Meaning |
|------|---------|
| `--theme PATH` | Record a theme project in `docs.toml` |
| `--force` | Overwrite an existing `docs.toml` |

## `epresso serve`

Serve an already-built `dist/` directory — **no build**. Use it to check exactly
what a deploy will serve, or to preview a build produced elsewhere.

```bash
epresso build && epresso serve
epresso serve --port 5000
```

| Flag | Meaning |
|------|---------|
| `--host H` | Host to bind (default `127.0.0.1`) |
| `--port N` | Preferred port (default 4321; the next free port is used if busy) |

Unlike `epresso preview`, it never loads the project or rebuilds — it fails if
`dist/` does not exist.

## `epresso build`

Build the site into `dist/`. Builds are deterministic and incremental; `--clean`
starts from scratch.

```bash
epresso build
epresso build --perf
epresso build --profile --profile-out epresso-profile.pstats
```

| Flag | Meaning |
|------|---------|
| `--clean` / `--no-clean` | Clean `dist/` before building (default: clean) |
| `--env NAME` | Environment (loads `site.<env>.toml` + `.env.<env>`; default `production`) |
| `--perf` | Print detailed build-phase timings |
| `--profile` | Run the build under `cProfile` and print the hottest frames |
| `--profile-out PATH` | Where `--profile` writes its stats file (default `epresso-profile.pstats`) |

See [Incremental builds & caching](/guides/build/incremental/) and
[Performance](/concepts/performance/).

## `epresso dev`

Run the Starlette development server with WebSocket live reload. It shares the
production incremental engine, so an edit re-renders only what changed.

| Flag | Meaning |
|------|---------|
| `--host H` | Host to bind (default `127.0.0.1`) |
| `--port N` | Preferred port (default 4321; the next free port is used if busy) |
| `--env NAME` | Environment (default `development`) |

Pages served by this server show the [dev toolbar](/guides/build/dev-toolbar/).

## `epresso preview`

Build (production environment) then serve the static `dist/` — exactly what a
deploy will serve, without the dev server's live reload.

| Flag | Meaning |
|------|---------|
| `--host H` | Host to bind (default `127.0.0.1`) |
| `--port N` | Preferred port (default 4321; the next free port is used if busy) |
| `--env NAME` | Environment (default `production`) |

## `epresso check`

Validate configuration and content, then list each collection and route. It
exits non-zero on a config/content error, so it is useful as a CI gate before a
build.

| Flag | Meaning |
|------|---------|
| `--env NAME` | Environment (default `production`) |

## `epresso layers`

List the external component/layout layers resolved from `[layers] use`, in
precedence order — the site's own `components/` and `layouts/` win, then the
layers in the order listed. See [Layers](/guides/extending/layers/).

| Flag | Meaning |
|------|---------|
| `--env NAME` | Environment (default `production`) |

## `epresso inspect`

Print the build graph — every route and its content → route edges — without
writing any output. Use it to see why a page is rebuilt (incremental fan-out).

```bash
epresso inspect                    # JSON
epresso inspect --format dot | dot -Tsvg -o graph.svg
```

| Flag | Meaning |
|------|---------|
| `--format json\|dot` | Output format (default `json`) |

## `epresso deploy`

Build and deploy the site. The default (and only current) provider is GitHub
Pages: it builds into `dist/`, commits it to a `gh-pages` branch, and pushes.

```bash
epresso deploy
epresso deploy --no-push        # build + commit locally, don't push
```

| Flag | Meaning |
|------|---------|
| `--provider NAME` | Deploy provider (only `gh-pages` today) |
| `--remote NAME` | Git remote to push to (default `origin`) |
| `--branch NAME` | Branch to publish (default `gh-pages`) |
| `--no-push` | Build + commit but do not push |

To publish with GitHub Actions instead of a branch, see the repository's
[`deploy-docs.yml`](https://github.com/nikoshell/epresso/blob/main/.github/workflows/deploy-docs.yml)
workflow.

## `epresso new`

Scaffold a project from a template, a theme name, a git URL, or a local
directory. Interactive when the arguments are omitted.

```bash
epresso new                        # interactive
epresso new basic mysite
epresso new docs mysite
epresso new github:nikoshell/epresso-theme-docs mysite
epresso new github:nikoshell/epresso-theme-docs@v1 mysite   # pinned to a tag
epresso new -y                     # non-interactive: basic template, current dir
```

| Argument / flag | Meaning |
|-----------------|---------|
| `template` | A built-in template (`basic`, …), a theme name, a git URL, or a directory path |
| `dest` | Destination directory (prompted when omitted) |
| `--yes` / `-y` | Skip prompts: basic template, current directory |

See [Start from a template](/guides/themes/from-template/).

## `epresso init`

Scaffold a blank project in `root` (default `.`): a `site.toml`, `pages/`,
`content/`, `public/` and `.gitignore` — no theme and no content, so you build
the layout yourself.

## `epresso clean`

Remove `dist/` and the `.cache` build cache. Running it twice is safe.

## `epresso version`

Print the epresso version. The same value is shown in the footer when
`[theme.footer] debug = true`.

## `epresso fmt`

Formats `.ep` files to the canonical structure: **frontmatter → HTML body →
`<script>` → `<style>`**, each section separated by a single blank line, plus
basic whitespace hygiene (strip trailing whitespace, ensure one trailing newline).
Section *content* (markup, CSS, JS, frontmatter Python) is preserved verbatim.

```bash
epresso fmt                 # format all .ep under the current directory
epresso fmt components/ pages/      # format specific files/dirs
epresso fmt --check .       # report files that would change; don't write (exit 1 if any)
epresso fmt --expand .      # reflow the body: one child per line (no extra deps)
epresso fmt --full .        # also format section contents (frontmatter/HTML/CSS/JS)
epresso fmt --stdin         # read one .ep source from stdin, write to stdout
```

`--stdin` is for editor integrations (the bundled VS Code extension uses it to
format the buffer without touching disk); it reads one `.ep` source from stdin
and writes the result to stdout. It cannot be combined with `--check`.

A layout — a document shell with `<html>/<head>/<body>` — is only
whitespace-normalised: its `<style>`/`<script>` are positional and never
reordered. `--check` is CI-friendly: it exits non-zero when any file needs
formatting.

## `epresso lsp`

A dependency-free Language Server for `.ep` files, speaking LSP on stdin/stdout
(no extra packages). It reports the same problems the build enforces — forbidden
Jinja composition (`{% extends %}`, `{% include %}`, `{% macro %}`, …), the
one-root-per-branch file shape, per-kind sidecar caps, and Python syntax errors
in the frontmatter — and offers `textDocument/formatting` backed by
`epresso fmt`.

```bash
epresso lsp        # speak LSP on stdin/stdout
```

Point any LSP-capable editor at it; see [Editor setup](/guides/editor-setup/).
The bundled VS Code extension and a small Neovim config snippet both use it.

### `epresso fmt --expand`

`--expand` reflows the HTML body: an element whose content is **markup only**
(no literal text) gets one child per line, Jinja blocks spread across lines, and
a lone interpolation moves onto its own line. No blank lines are added.

```epresso
---
---
<div class="card">
    {% if props.icon %}<Icon name={tone.icon} />{% endif %}
    <p>{{ props.title }}</p>
</div>
```

becomes

```epresso
---
---
<div class="card">
    {% if props.icon %}
        <Icon name={tone.icon} />
    {% endif %}
    <p>
        {{ props.title }}
    </p>
</div>
```

Elements that contain **literal text** (`<p>Hello <b>world</b></p>`) are left
alone, so prose keeps its line wrapping, and `<pre>` / `<script>` / `{% raw %}`
bodies are never re-indented. Siblings that the author glued together with no
whitespace are kept glued, because that whitespace is significant.

This changes the whitespace in the *rendered* HTML — harmless inside block and
flex/grid containers, but visible between inline elements. It is therefore
off by default; `--full` implies it. The reflow is conservative: if the result
would change any non-whitespace character, the file is left untouched.

### `epresso fmt --full`

`--full` additionally formats each section's **content** by reusing dedicated
tools, shipped as the optional `[fmt]` extra:

| Section | Tool |
|---------|------|
| frontmatter (Python) | `ruff format` |
| HTML body | `--expand` reflow + `djhtml` |
| CSS (`<style>`) | `cssbeautifier` |
| JS (`<script>`) | `jsbeautifier` |

`--full` implies `--expand`.

```bash
pip install -e .[fmt]
epresso fmt --full .
```

Jinja (`{{ }}`/`{% %}`/`{# #}`) is preserved throughout. If the `[fmt]` deps are
missing, `--full` formats whatever is available and skips the rest.
