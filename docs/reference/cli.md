---
order: 420
---

# CLI

epresso ships a single `epresso` command with subcommands:

| Command | Description |
|---------|-------------|
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
| `epresso inspect` | Inspect the build graph (routes + content → route edges) |
| `epresso deploy` | Build and deploy (GitHub Pages by default) |
| `epresso version` | Print the version |

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
