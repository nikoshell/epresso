---
order: 334
---

# Incremental builds & caching

epresso builds are **deterministic** (same source + config → same output) and
**incremental** (a content edit re-renders only the affected pages).

## How it works

- Every content entry has a **digest** over its body + data.
- The build records a dependency graph: each route depends on the collections
  and entries it consumed (via `get_collection` / `get_entry`).
- On the next build, routes whose dependencies haven't changed are **reused**
  from the cache instead of re-rendered.
- The cache is dropped wholesale when the *config* or any *template/component*
  changes — including a file in a [layer](guides/extending/layers.md) — so
  editing a component re-renders every route.

## Cache

The incremental cache lives in `.cache/` (gitignored; not removed by `epresso clean`).
A clean build (`epresso build --clean`) re-renders everything so side-effect
outputs (islands, assets, images) are regenerated.

## Determinism

Outputs use content-hashed filenames and stable ordering, so identical source
always produces identical output — ideal for caching and reproducible deploys.

## `epresso clean`

Removes `dist/` and the `.cache` build cache.
