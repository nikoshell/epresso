---
order: 110
---

# Project structure

By default everything lives at the project root. `site.toml` and
`content.config.py` are always at the root — they are project configuration,
not source.

```tree
site.toml            # configuration
content.config.py    # define collections + schemas (Pydantic)
pages/               # routes (.ep, .md, .py endpoints)
layouts/             # layout templates (.ep) — resolved as components too
components/          # UI components (.ep), resolved by basename across subdirs
  primitives/        #   base building blocks (IconButton, Badge)
  controls/          #   interactive controls (SearchButton, ThemeToggle, Pager)
  patterns/          #   feature patterns (Markdown, Highlight, SearchOverlay, …)
  navigation/        #   navigation (Nav, Tree, Breadcrumbs, Toc)
  structure/         #   page regions (Header, Footer)
content/             # content collections (markdown / JSON / YAML / TOML)
styles/              # global stylesheets (global.css)
assets/              # buildable assets (images, js); top-level files land at root
public/              # files copied verbatim to the output root
```

## `public/`, `assets/` or `styles/`?

The three asset directories have distinct jobs:

| Directory  | Processed?                    | Used for |
|------------|-------------------------------|----------|
| `public/`  | copied verbatim to the root   | favicon, `robots.txt`, fonts, images you don't want transformed |
| `assets/`  | processed at build            | `image()` sources (responsive WebP), `asset()` references (content-hashed CSS/JS), bundle entries |
| `styles/`  | processed at build            | the global stylesheet entry (`global.css`) |

* **`public/`** files are never hashed, minified, or rewritten — `public/f.pdf`
  lands at `/f.pdf`. This is the escape hatch for anything the pipeline should
  not touch.
* **`assets/`** is where build-time processed files live. Top-level files in it
  are still copied verbatim to the output root (`assets/robots.txt` →
  `/robots.txt`), so it can serve as a drop-in replacement for `public/` when you
  want everything in one place. Subdirectories (`assets/images/`, `assets/js/`)
  are referenced via `image()` / `asset()` and may be content-hashed.
* **`styles/`** is a stylesheet root. `asset()` looks in `assets/` first and then
  `styles/`, so `asset('global.css')` resolves `assets/global.css` or
  `styles/global.css` — whichever exists.

Each directory is **optional**. A text-only site needs none of them; a site that
only uses `public/` can delete `assets/` and `styles/`.

## Collections

Collections are defined in `content.config.py`; a directory like `blog/` becomes
a collection by pointing `define_collection(..., base="./blog")` at it. Collection
`base` paths are relative to the project root.

## Layers

`components/` and `layouts/` can also come from external sources — another
directory, an installed package, or a git repo — declared in `[layers]`:

```toml
[layers]
use = ["./vendor/components", "pkg:epresso_ui", "github:owner/epresso-components@v1"]
```

The site's own roots are always searched first. See
[Layers](guides/extending/layers.md).
