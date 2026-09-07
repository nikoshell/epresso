# components/

UI components and layouts live under `components/`, organized by role (design-system style).
Components are referenced by basename (`<IconButton />`, `<Nav />`, `<Pager />`) from any
template — epresso resolves them recursively across these subdirectories, so you can
move files without changing usages.

| Directory | Purpose | Examples |
|-----------|---------|----------|
| `primitives/` | Smallest reusable base blocks | `IconButton` |
| `controls/` | Interactive controls | `SearchButton`, `ThemeToggle`, `PageActions`, `Pager` |
| `patterns/` | Self-contained feature patterns (markup + CSS + JS) | `SearchOverlay`, `ImageLightbox`, `CodeHead`, `Highlight` |
| `navigation/` | Navigation pieces | `Nav`, `Breadcrumbs`, `Toc` |
| `structure/` | Page regions | `Header`, `Footer` |
| `sections/` | Marketing sections (Hero, Pricing, …) — reserved for future use | |
| `layouts/` | Layout templates, extended by pages | `Base`, `Doc` |

**How to categorize a component:**

- **`primitives/`** — the smallest reusable building block (a base button).
- **`controls/`** — an interactive element the user operates (buttons, toggles, nav links).
- **`patterns/`** — a composed, self-contained feature that bundles markup + CSS + JS (a search overlay, a lightbox, a code block).
- **`navigation/`** — how users move around the site (sidebar, breadcrumbs, ToC).
- **`structure/`** — a distinct region of a page (header, footer).
- **`sections/`** — larger marketing/page sections (Hero, Features, Pricing…).
- **`layouts/`** — document shells that pages extend.

Every component owns its markup, scoped CSS, and behavior script (self-contained).
The `components` and `layouts` build roots are configured in `site.toml`
(`[build] components = "components"`, `[build] layouts = "components/layouts"`).
