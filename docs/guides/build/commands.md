---
order: 331
---

# Commands

## Development server

```bash
epresso dev
```

Starts a Starlette dev server with **WebSocket live reload**. It shares the
production incremental engine, so content/template edits are picked up
automatically. Use `--host` / `--port` / `--env`.

## Build

```bash
epresso build
```

Produces a deterministic, incremental build into `dist/`. `--clean` forces a
full rebuild; `--env <name>` selects a per-environment config.

## Serve

```bash
epresso preview   # build, then serve dist/ statically
epresso docs      # build + serve the documentation on port 4321
```

## Check

```bash
epresso check
```

Validates configuration and content, then lists collections and routes.

## Clean

```bash
epresso clean     # remove dist/ and the .cache build cache
```

## Deterministic + incremental

Builds are deterministic (same input → same output) and incremental (edits
re-render only affected pages) — see [Incremental builds & caching](../guides/build/incremental.md.
