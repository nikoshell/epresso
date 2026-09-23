# bench

Measurement suite for the epresso render pipeline. It exists to **find and
compare costs**, not to gate CI — `scripts/bench.py` remains the regression gate.

## Fixtures

| file | what it stresses |
| --- | --- |
| `small.md` | floor: one heading, one paragraph, one link |
| `medium.md` | a normal page: 12 sections with headings, tables, lists, code, images |
| `large.md` | 120 sections (~134 KB) — how cost scales with page size |
| `code-heavy.md` | almost entirely fenced code, several languages — Pygments |
| `components.md` | allow-listed component tags + a code component |
| `docs.md` | a documentation-shaped page (the shape most sites build) |

## Phases

`phases` calls each stage's **own function**, so a slow row points at one module:

```
file loading · frontmatter (YAML) · Markdown parsing · Markdown rendering ·
Pygments (plain) · Pygments (code component) · component expansion ·
Jinja (compile + render) · Jinja (warm render) · HTML postprocessing ·
filesystem output · total (render_markdown)
```

`Markdown parsing` is `md.parse`; `Markdown rendering` is
`renderer.render(tokens, …)` on those tokens. Their sum is one `md.render`.

```
python bench/run.py phases
python bench/run.py phases --fixture large --runs 10
```

## Scale

`scale` generates a throwaway project with N pages and measures the real
`Site.load` + `Site.build` path. `cold` is a clean build with an empty cache;
`warm` is an incremental rebuild. The columns are `BuildResult.perf` phases
(also shown by `epresso build --perf`).

```
python bench/run.py scale --sizes 1,10,100
python bench/run.py scale --sizes all              # 1 .. 10000
python bench/run.py scale --shape ep --sizes 1,10  # .ep pages: Jinja + components
```

Shapes: `docs` (Markdown), `code` (Markdown, code-heavy), `ep` (`.ep` pages that
use a layout and a component).

`--sizes all` builds 1,000 and 10,000 pages and will take minutes; the default is
`1,10,100`.

## Terminology

- **cold** — first invocation in a fresh process: no warm caches, cold page cache.
  One sample, so noisy.
- **warm** — median of the remaining runs in the same process. Trust this one.

A `cold/warm` ratio near 1 means the phase has no warm cache (e.g. Pygments
before memoisation); a high ratio means the first call pays a one-off cost
(imports, YAML/Pygments lexer setup).

## Output

```
python bench/run.py all --json bench/results.json
python bench/run.py scale --sizes 200 --summary bench/summary.md
```

`results.json` carries every phase and scale row for diffing across commits.
`--summary` writes a markdown report (a phase table plus a Mermaid `pie` of the
phase split) intended for `$GITHUB_STEP_SUMMARY`. The `pie` is deliberate:
GitHub's pinned Mermaid version does not render `xychart-beta`, so a line/bar
chart would silently fail to appear.

CI runs `scale --sizes 200 --shape docs` on every push to `main` and every PR,
appends the summary to the run page, and uploads `results.json` as an artifact.

Use `python -m epresso build <theme> --perf` for a real theme, and
`--profile` / `py-spy` when a row points at something worth a flame graph.
