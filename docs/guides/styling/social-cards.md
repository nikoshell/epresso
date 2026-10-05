---
order: 324
description: Generate og:image preview cards for link shares with the epresso_social plugin.
---

# Social cards

`epresso_social` draws the preview image link shares show (Open Graph
`og:image`, Twitter/X `summary_large_image`): a 1200×630 PNG per section, per
page or per collection. The docs theme enables it. Any site can enable it too:

```toml
plugins = ["epresso_social"]

[site]
url = "https://example.com/"   # cards are linked by absolute URL
```

It needs Pillow: `pip install 'epresso[images]'`. Without Pillow the build warns
once and pages keep their existing image.

## Which pages share a card

```toml
[plugin.epresso_social]
cards = "sections"   # default
```

| `cards` | Cards drawn | Title on the card |
|---|---|---|
| `sections` | one per top-level URL segment (`/guides/…`) | the section's landing page title, else the folder name |
| `all` | one per page | the page title and description |
| `collection` | one per content collection | the collection name, or `[plugin.epresso_social.titles]` |

The homepage, and pages outside any section or collection, get the **site card**
(site name and description). A page that sets its own `og:image` keeps it. With
`[plugin.epresso_docs] base = "/docs/"`, sections are counted under the base.

```toml
[plugin.epresso_social.titles]   # collection mode
docs = "Documentation"
```

## Look

```toml
[plugin.epresso_social]
background = "#0f1117"
color = "#e8ecf1"
accent = "#3ecf8e"            # site name and the bottom bar
logo = "public/logo.png"      # PNG; an SVG logo is skipped (the site name shows)
background_image = "card.png" # PNG drawn under the text
font = "fonts/Inter.ttf"      # default: Space Grotesk + IBM Plex Sans
```

The layout is fixed: logo and site name at the top, the title (up to three lines;
it shrinks to fit), the description (two lines), and an accent bar.

## Builds and caching

Cards are written to `dist/social/` and cached in `.cache/social/`, so a rebuild
only draws cards whose text or options changed. `epresso dev` points pages at the
cards but doesn't draw them; set `dev = true` to draw them there too.
