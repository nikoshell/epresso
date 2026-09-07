# epresso — Neovim / Vim syntax highlighting

`.ep` files are **Python frontmatter** (`--- … ---`) + a **Jinja2/HTML body**. This
plugin highlights the frontmatter as Python and the body as HTML — with Jinja for
template tags and CSS/JS inside `<style>`/`<script>` — and sets the `.ep` filetype
so `:setf`, `gcc`, indentation and any `ftplugin` hooks apply.

## Files

```
extras/nvim/
├── ftdetect/epresso.vim    # `*.ep` -> filetype 'epresso'
├── syntax/epresso.vim      # Python frontmatter + HTML (CSS/JS in <style>/<script>) + Jinja
├── ftplugin/epresso.vim    # commentstring + python-ish indentation options
└── indent/epresso.vim      # python-based indentation
```

## Install

Add `extras/nvim` to Neovim's `runtimepath`. Because filetype detection is
global, **every epresso project** (any `.ep` file anywhere) gets highlighted once
this is on the runtimepath — you don't copy files into each project.

### Simplest — append to runtimepath (e.g. in `~/.config/nvim/init.lua`)

```lua
vim.opt.rtp:append("/absolute/path/to/epresso/extras/nvim")
```

### LazyVim / lazy.nvim

Declare it as a local plugin so lazy.nvim manages it and compiles the rtp:

```lua
{ dir = "/absolute/path/to/epresso/extras/nvim", name = "epresso" },
```

(or add the same `dir` to your `{ import = "lazy.plugins" }` list.)

### Classic Vim (non-Neovim)

Add it to `runtimepath` in `~/.vimrc`:

```vim
set runtimepath+=/absolute/path/to/epresso/extras/nvim
```

## If epresso is installed as a Python package

The runtime files ship under `extras/nvim/` in the source tree. If you install
epresso from a wheel/site-packages, the path is
`<site-packages>/epresso/../` … — in that case, keep a checkout on disk (or copy the
four files into `~/.config/nvim/after/`) and point the runtimepath at it.

## Verifying

Open any `.ep` file and check:

```vim
:set filetype?   " -> filetype=epresso
:echo hlexists('epressoFrontmatter')   " -> 1
```

The `---` delimiter lines render in the `Comment` colour; the frontmatter code
uses Python groups; the body uses HTML groups, with Jinja groups for template
tags and CSS/JavaScript groups inside `<style>`/`<script>`.
