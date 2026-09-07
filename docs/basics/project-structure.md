# Project structure

```tree
public/              # files copied verbatim to the output root (file.pdf → /file.pdf)
content/             # content collections (markdown / JSON / YAML / TOML)
components/          # UI components + layouts — resolved by basename across subdirs
  primitives/        #   base building blocks (IconButton, Badge)
  controls/          #   interactive controls (SearchButton, ThemeToggle, PageActions, Pager)
  patterns/          #   feature patterns (Markdown, Highlight, CodeHead, SearchOverlay, …)
  navigation/        #   navigation (Nav, Tree, Breadcrumbs, Toc)
  structure/         #   page regions (Header, Footer)
  sections/          #   marketing sections (Hero, Pricing, …) — reserved
  layouts/           #   layout templates (Base, Doc) — extended by pages
lib/                 # theme Python helpers (nav, md, docs, repo, pygments_theme)
assets/              # buildable assets (images, js); top-level files land at root
pages/               # routes
  posts/[post].ep    #   dynamic route
  about.ep           #   static .ep page
  page.md            #   direct markdown page
  index.ep           #   home page
  rss.xml.ep         #   .ep endpoint (frontmatter exports get() → content_type, body)
styles/              # global stylesheet (global.css) — tokens, fonts, resets
site.toml            # configuration
content.config.py    # define collections + schemas (Pydantic)
```

Collections are defined in `content.config.py`; a top-level directory like `blog/`
becomes a collection by pointing `define_collection(..., base="./blog")` at it.
