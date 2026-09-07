# Editor setup

epresso ships editor support for the `.ep` file format (Python frontmatter +
Jinja body + optional `<style>` / `<script>`).

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

## Other editors

No official grammar is shipped yet for VS Code or other editors. The `.ep`
format combines Python (frontmatter) and Jinja/HTML (body), so a
Python + Jinja/HTML grammar is a reasonable approximation. If you'd like a
TextMate/VS Code grammar, that's a good candidate to contribute.
