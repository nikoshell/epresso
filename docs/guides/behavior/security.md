# Security

epresso produces a **static site**, so there is no server, request, or database
surface to attack. The main concerns are output quality and headers.

- **Escaping by default** — template `{{ … }}` output is auto-escaped; raw HTML is
  opt-in via `| safe`/`Markup`, so XSS from content is avoided by default.
- **Trusted build input** — content/markdown is build-time input you author. If you
  render user-provided Markdown, sanitize output or avoid `| safe`.
- **Build-time env only** — environment variables are read at build time and are
  **not** shipped to the browser (see [Environment Variables](guides/build/environment-variables.md).
- **Content Security Policy** — add a CSP via a `<meta http-equiv="Content-Security-Policy">`
  in your layout `<head>`, or as a response header from your static host.

## Sessions / auth

There are no sessions or server actions — it's all static files. Anything needing
per-user auth must happen in your hosting middleware/proxy or a client-side auth
flow against an external service.
