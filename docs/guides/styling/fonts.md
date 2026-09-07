# Fonts

There is no automatic font-fetching or font-optimization pipeline (no subsetting,
no remote-provider fetch). Fonts are handled the same as any static asset:

- **Local fonts**: put the font files under `public/` (or `assets/`) and reference
  them from your global stylesheet with `@font-face`; `asset()` gives you
  content-hashed URLs. See [Styling and CSS](styling.md and [Images](images.md.
- **Remote fonts**: link the provider's stylesheet in your layout `<head>` as
  usual.

The docs theme self-hosts its fonts via `styles/global.css` + `public/`.
