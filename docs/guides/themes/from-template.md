---
title: Start from a template
order: 20
description: Scaffold a full site from a ready-made theme with epresso new.
---

`epresso new` scaffolds a project from a **starter template** or a **theme** — a
complete, runnable site — into a new directory, and strips its git history. You
own the result outright.

Run it with no arguments for an interactive prompt:

```bash
epresso new
```

```
Where should we create your new project?
.
How would you like to start your new project?
  1. A basic, helpful starter project (recommended)
  2. Use the blog template
  3. Use the docs template
  4. Use the minimal (empty) template
```

| Template | What you get |
|---|---|
| `basic` | Directories, `site.toml`, a page, a `Base` layout and `content.config.py` |
| `docs` | The documentation theme (ships with epresso under `themes/`) |
| `blog` | The blog theme |
| `minimal` | `site.toml` + one bare page — nothing else |

Skip the prompts by passing the template and destination, or `-y` for the basic
starter in the current directory:

```bash
epresso new docs mysite     # a documentation site
epresso new minimal mysite  # the smallest buildable project
epresso new -y              # basic starter, current directory
cd mysite && epresso dev
```

A theme can also be a git source or a local directory — useful while a theme has
no registry entry yet:

```bash
epresso new github:nikoshell/epresso-theme-docs mysite
epresso new ./epresso-theme-mytheme mysite
```

See the available names:

```bash
epresso new --help          # Template (basic, blog, docs, minimal) …
```

## What you get

The scaffold *is* a normal epresso project, so everything in
[Create a new website](guides/themes/new-website.md) applies. A docs theme, for
example, ships far more than the blank scaffold:

```tree
mysite/
  site.toml
  content.config.py
  pages/                      # routes, including dynamic ones
  layouts/                    # Base.ep, Doc.ep — the page shells
  components/
    primitives/               # Icon, IconButton
    controls/                 # Pager, SearchButton, ThemeToggle
    navigation/               # Breadcrumbs, NavAccordion, Toc
    patterns/                 # Markdown, Highlight, CodeHead, SearchOverlay
    structure/                # Header, Footer
  styles/                     # global stylesheet + design tokens
  public/                     # favicon, etc.
```

Build and preview it as production:

```bash
epresso build
epresso preview
```

## Customizing a template

You are editing a copy, so change anything:

1. **Identify it** — `site.toml`: `[site] name`, `url`, `repository`, `branch`.
2. **Adjust the shell** — `layouts/Base.ep` (the whole document) and
   `layouts/Doc.ep` (the documentation page frame).
3. **Restyle** — `styles/` holds the tokens and global CSS. `[assets] css`
   names the entry point.
4. **Delete what you don't need** — demo pages under `pages/`, unused
   components. Nothing else depends on them.
5. **Add your content** — drop Markdown into `content/` and point a collection
   at it in `content.config.py`.

Because it is a copy, upstream theme changes are **not** picked up. If you want
to keep receiving updates while overriding only some files, that is the planned
layer mode — a *Coming soon* tutorial, visible in local previews.

## How `epresso new` fetches a theme

`<theme>` is one of three things:

| Form | Example |
|---|---|
| A registry name | `docs`, `blog` |
| A git URL | `github:owner/repo`, `https://github.com/owner/repo.git`, `git@github.com:owner/repo.git` |
| A local directory | `./epresso-theme-mytheme`, `~/themes/blog` |

Add `@ref` to a git source to pick a branch or tag:

```bash
epresso new github:nikoshell/epresso-theme-docs mysite
epresso new github:nikoshell/epresso-theme-docs@v1 mysite     # pinned to a tag
epresso new git@github.com:nikoshell/epresso-theme-docs.git mysite
epresso new ./epresso-theme-mytheme mysite
```

Resolution is: a **local directory is copied** (git history stripped); anything
else is `git clone --depth=1 <repo> <dest>`, with `--branch <ref>` added only
when a ref is given — so a plain URL uses the repository's default branch.

A **registry name** maps to a repository in `src/epresso/themes.py`, and is the
only form that can additionally fall back to a bundled starter inside epresso:

```python
REGISTRY = {
    "docs": ("<repo>/themes/docs", "main"),          # ships in this repository
    "blog": ("...epresso-theme-blog", "main"),         # sibling checkout / git URL
}
```

`docs` ships with epresso under `themes/`, so `epresso new docs` copies it
directly — no clone and no network. Other names resolve to a **local path** to a
sibling checkout while developing, or a **published git URL**.

The docs theme specialises in rendering an existing Markdown tree (it is what
builds these pages), so a scaffolded copy points at its enclosing repository via
`[theme] repo` / `[theme] docs_dir` in `site.toml`. After
`epresso new docs mysite`, set those to your repository and docs folder — or
replace them with your own pages — before building.

## Next steps

- [Create a theme](guides/themes/create-a-theme.md) — turn your own project into
  something `epresso new` can scaffold.
- [Create a new website](guides/themes/new-website.md) — the blank-project path.
