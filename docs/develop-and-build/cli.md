# CLI

epresso ships a single `epresso` command with subcommands:

| Command | Description |
|---------|-------------|
| `epresso init` | Scaffold a blank project |
| `epresso new <theme> <dest>` | Scaffold from a theme (docs/blog) |
| `epresso dev` | Development server with live reload |
| `epresso build` | Deterministic + incremental production build |
| `epresso preview` | Build then serve `dist/` (production preview) |
| `epresso docs` | Build + serve the documentation (port 4321) |
| `epresso clean` | Remove `dist/` and the build cache |
| `epresso check` | Validate config + content, list routes |
| `epresso fmt` | Format `.ep` files to the canonical section structure |
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
epresso fmt --full .        # also format section contents (frontmatter/HTML/CSS/JS)
```

Layouts (`{% extends %}` or a document shell with `<html>/<head>/<body>`) are
only whitespace-normalised — their `<style>`/`<script>` are positional and never
reordered. `--check` is CI-friendly: it exits non-zero when any file needs
formatting.

### `epresso fmt --full`

`--full` additionally formats each section's **content** by reusing dedicated
tools, shipped as the optional `[fmt]` extra:

| Section | Tool |
|---------|------|
| frontmatter (Python) | `ruff format` |
| HTML body | `djhtml` (Jinja-aware) |
| CSS (`<style>`) | `cssbeautifier` |
| JS (`<script>`) | `jsbeautifier` |

```bash
pip install -e .[fmt]
epresso fmt --full .
```

Jinja (`{{ }}`/`{% %}`/`{# #}`) is preserved throughout. If the `[fmt]` deps are
missing, `--full` formats whatever is available and skips the rest.
