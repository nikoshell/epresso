---
order: 343
---

# Middleware

epresso is a **build-time, static generator** — there is no per-request
middleware (`onRequest`) or server runtime to intercept requests.

The analog is the **build-time Plugin API**: a project or plugin module can hook
the build lifecycle (`on_setup`, `before_load`, `after_load`, `before_build`,
`after_build`, `on_assets`). See [Plugins](plugins.md.

For anything that must happen per-request (auth, redirects by header, edge
logic), serve the generated `dist/` behind your own middleware/proxy — epresso
just produces the static files.
