# epresso for VS Code

Language support for epresso's `.ep` format (Python frontmatter + Jinja/HTML body
+ component tags + optional `<style>` / `<script>` sidecars).

## Features

- **Syntax highlighting** — Python frontmatter; HTML + Jinja body; component tags
  (`<Card>`, `<Card:dir/>`, `<slot/>`, `<Fragment>`, `<>…</>`); JSX `{expr}` props;
  `<style>` (CSS) and `<script>` (JS) sidecars.
- **Diagnostics** — a bundled LSP client runs `epresso lsp` and shows the same
  rules the build enforces (forbidden Jinja composition, one-root-per-branch
  file shape, sidecar caps, frontmatter syntax).
- **Formatting** — *Format Document* and format-on-save run `epresso fmt --stdin`
  and replace the buffer with the canonical layout (body → script → style).

Both features need the `epresso` CLI on `PATH` (or a configured path); without it
the extension reports the problem and leaves the buffer untouched.

## Install

### From source (development)

1. Open the `extras/vscode` folder in VS Code.
2. Press `F5` to launch an Extension Development Host, then open any `.ep` file.

### From a `.vsix`

```bash
cd extras/vscode
npx @vscode/vsce package            # → epresso-0.1.0.vsix
code --install-extension epresso-0.1.0.vsix
```

## Diagnostics

The extension starts `epresso lsp` (a standard-library Language Server bundled
with epresso) and surfaces its diagnostics as VS Code problems. It covers the
same rules the build enforces:

| Code          | Meaning                                                        |
|---------------|----------------------------------------------------------------|
| `composition` | forbidden Jinja composition (`{% extends %}`, `{% include %}`, …) |
| `file-shape`  | an `.ep` file renders more than one root in a branch            |
| `sidecar`     | more than one scoped `<style>` / global `<style>` / `<script>`  |
| `syntax`      | Python syntax error in the frontmatter                          |

| Setting                        | Default     | Effect                                    |
|--------------------------------|-------------|-------------------------------------------|
| `epresso.lsp.enable`           | `true`      | run the language server                   |
| `epresso.lsp.executablePath`   | `epresso`   | CLI used to launch `epresso lsp`          |

If the server cannot start, a one-time warning appears and highlighting/formatting
keep working.

## Formatting

Formatting shells out to the `epresso` CLI, which must be installed and on `PATH`
(or point `epresso.format.executablePath` at it).

| Setting                           | Default    | Effect                                            |
|-----------------------------------|------------|---------------------------------------------------|
| `epresso.format.executablePath`   | `epresso`  | CLI to run                                        |
| `epresso.format.expand`           | `false`    | pass `--expand` (reflow the body one child/line)  |
| `epresso.format.full`             | `false`    | pass `--full` (also format sections; needs `epresso[fmt]`) |

Enable format-on-save for the language:

```json
"[epresso]": {
  "editor.formatOnSave": true
}
```

If `epresso` is not found, VS Code reports an error and leaves the buffer
untouched.

## Verifying highlighting

Run **Developer: Inspect Editor Tokens and Scopes** and click a token:

| Region                       | Scope                                             |
|------------------------------|---------------------------------------------------|
| frontmatter code             | `meta.embedded.block.python.epresso`              |
| component tag name           | `entity.name.tag.component.epresso`               |
| `<slot>`                     | `entity.name.tag.slot.epresso`                    |
| Jinja delimiters             | `punctuation.section.embedded.*.jinja.epresso`    |
| Jinja keyword                | `keyword.control.jinja.epresso`                   |
| Jinja filter                 | `support.function.filter.jinja.epresso`           |
| `<style>` body               | `source.css`                                      |
| `<script>` body              | `source.js`                                       |

## Notes and limitations

- The comment toggle uses `#` (frontmatter Python) and `{# … #}` (Jinja). HTML
  `<!-- … -->` comments are still passed through and highlighted by the HTML
  grammar.
- `{expr}` prop values are Jinja expressions (scoped as embedded Python).
- Jinja inside plain HTML tag attributes (`<a href="{{ url(...) }}">`) is handled
  by an injection grammar scoped to `text.epresso`, so plain `.html` files are
  unaffected.
- TextMate grammars are standard JSON and can be reused by other editors that read
  `.tmLanguage.json`.

## Publishing

This extension is not published to the Marketplace from this repo. To publish, set
a real `publisher` in `package.json` and run `vsce publish`.

## License

MIT — see [`LICENSE`](./LICENSE).
