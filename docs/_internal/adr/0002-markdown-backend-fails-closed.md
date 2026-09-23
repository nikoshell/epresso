# 2. The markdown backend fails closed, it does not fall back

Status: Accepted

Date: 2026-09-19

## Context

`[markdown] backend` selects the renderer: `native` (the built-in markdown-it-py
pipeline) or `rust`, an optional accelerator that is not part of this
distribution. Selecting a backend that is not installed forces a choice — fall
back to `native` silently, or stop the build.

## Decision

Stop the build. `markdown._backend()` raises a `ContentError` naming the backend
and the way out ("install the markdown accelerator, or set `[markdown] backend =
"native"`"). There is no fallback path.

The value stays a validated `Literal["native", "rust"]` on
`MarkdownConfig.backend`, so an unknown backend is rejected at config load rather
than at first render.

## Consequences

Positive:
- The same `site.toml` produces the same HTML everywhere: a build either uses the
  backend it asked for or it stops.
- A missing accelerator is reported where it is configured, not discovered later
  as an unexplained rendering difference.

Negative / migration:
- A site configured for `rust` will not build without the extra, even though
  `native` could have served it. That is the intended cost.
- `backend` is part of the config hash, so changing it invalidates the incremental
  and rendered-body caches. Correct, because a different renderer may render
  differently.

## Alternatives considered

1. **Silent fallback to `native`** — simplest, but makes output depend on which
   extras happen to be installed on the machine, with no signal. Builds stop being
   reproducible and the difference is hard to attribute.
2. **Fall back with a warning** — build warnings get scrolled past, and the output
   still differs. It does not solve the reproducibility problem.
3. **Auto-install the accelerator** — out of scope; a build should not mutate its
   own environment.

## Decision drivers

- Deterministic, reproducible builds are a core promise of epresso.
- A pluggable backend only pays off while the backend in use is explicit.
