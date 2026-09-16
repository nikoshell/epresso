# components/

UI components live under `components/`, organized by role (design-system style).
Components are referenced by basename (`<IconButton />`, `<Nav />`, `<Pager />`) from any
template — epresso resolves them recursively across these subdirectories, so you can
move files without changing usages. Document shells live in the top-level
`layouts/` directory.

| Directory | Purpose | Examples |
|-----------|---------|----------|
| `primitives/` | Smallest reusable base blocks | `IconButton` |
| `controls/` | Interactive controls | `SearchButton`, `PageActions`, `Pager` |
| `patterns/` | Self-contained feature patterns (markup + CSS + JS) | `SearchOverlay`, `ImageLightbox`, `CodeHead`, `Highlight` |
| `navigation/` | Navigation pieces | `Nav`, `Breadcrumbs`, `Toc` |
| `structure/` | Page regions | `Header`, `Footer` |
| `sections/` | Marketing sections (Hero, Pricing, …) — reserved for future use | |

**How to categorize a component:**

- **`primitives/`** — the smallest reusable building block (a base button).
- **`controls/`** — an interactive element the user operates (buttons, toggles, nav links).
- **`patterns/`** — a composed, self-contained feature that bundles markup + CSS + JS (a search overlay, a lightbox, a code block).
- **`navigation/`** — how users move around the site (sidebar, breadcrumbs, ToC).
- **`structure/`** — a distinct region of a page (header, footer).
- **`sections/`** — larger marketing/page sections (Hero, Features, Pricing…).

Every component owns its markup, scoped CSS, and behavior script (self-contained).
