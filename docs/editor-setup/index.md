# Editor setup

epresso ships editor support for the `.ep` file format (Python frontmatter +
Jinja body + optional `<style>` / `<script>`).

## Language server (LSP)

`epresso lsp` is a dependency-free Language Server (standard library only). It
reports the same problems the build enforces, live as you type:

- forbidden Jinja composition (`{% extends %}`, `{% include %}`, `{% macro %}`, …);
- the one-root-per-branch `.ep` file shape;
- per-kind sidecar caps (one scoped `<style>`, one `<style is:global>`, one `<script>`);
- Python syntax errors in the frontmatter.

It also answers `textDocument/formatting` with the canonical `epresso fmt`
output. Point any LSP-capable editor at it over stdio:

```bash
epresso lsp
```

## Neovim / Vim

Syntax highlighting is bundled under `extras/nvim/`. Add it to your runtimepath
once:

```lua
-- ~/.config/nvim/init.lua
vim.opt.rtp:append("/path/to/epresso/extras/nvim")
```

This provides filetype detection, syntax highlighting, indentation, and
ftplugin settings for `.ep` files. See `extras/nvim/README.md` for LazyVim
instructions.

To also get diagnostics and formatting in Neovim, attach the language server
(Neovim 0.8+ has a built-in LSP client, no plugin needed):

```lua
-- ~/.config/nvim/init.lua
vim.api.nvim_create_autocmd("FileType", {
  pattern = "epresso",
  callback = function()
    vim.lsp.start({
      name = "epresso",
      cmd = { "epresso", "lsp" },
      root_dir = vim.fs.dirname(vim.fs.find({ "site.toml" }, { upward = true })[1]),
    })
  end,
})
```

## VS Code

Syntax highlighting, **diagnostics** and formatting are bundled under
`extras/vscode/` (a zero-dependency extension: TextMate grammar + a tiny LSP
client + a formatter).

Run it from source — open `extras/vscode/` in VS Code and press `F5` to launch an
Extension Development Host — or package it once:

```bash
cd extras/vscode
npx @vscode/vsce package            # → epresso-0.1.0.vsix
code --install-extension epresso-0.1.0.vsix
```

**Diagnostics** come from the bundled language server, started automatically
(`epresso.lsp.enable`); it uses the `epresso` CLI from `PATH` (or
`epresso.lsp.executablePath`).

**Formatting** runs the `epresso` CLI, which must be installed and on `PATH`
(or set `epresso.format.executablePath`). Enable format-on-save for the language:

```json
"[epresso]": {
  "editor.formatOnSave": true
}
```

The extension covers Python frontmatter, HTML + Jinja, component tags
(`<Card>`, `<slot/>`, `<Fragment>`), `{expr}` props and the `<style>`/`<script>`
sidecars. See `extras/vscode/README.md` for settings and the scope reference.

## Other editors

The `.ep` grammar ships as standard TextMate JSON at
`extras/vscode/syntaxes/epresso.tmLanguage.json` (plus an injection grammar), so
any editor that reads `.tmLanguage.json` — Sublime Text, TextMate, IntelliJ,
Zed, … — can reuse it directly. The `.ep` format combines Python (frontmatter)
with Jinja/HTML (body); pointing such an editor at the TextMate grammar (or at a
Python + Jinja/HTML grammar) gives a close approximation.
