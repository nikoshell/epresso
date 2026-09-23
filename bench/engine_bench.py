"""MiniJinja vs Jinja2 on the real templates a docs page renders.

Captures every template an actual `Site.render_route` call renders, together
with the *real* context it was handed, then times repeated `render()` calls in
both engines. Also measures how much of a whole page render is template
evaluation at all — the ratio that decides whether swapping the engine can pay.

    .venv/bin/python bench/engine_bench.py [--reps 150] [--source docs]

Jinja2 always runs. The MiniJinja half needs `pip install minijinja`; without it
the script reports what MiniJinja refused and still prints the Jinja2 numbers
plus a marshalling probe (attribute access on Python objects across the FFI,
the pattern a MiniJinja port pays for on every render).

Why the "twin": MiniJinja's Python binding exposes filters/globals/tests but no
custom *statements*, so epresso's `{% component %}` block tag cannot compile.
The twin replaces each component tag with a variable holding that child's
pre-rendered HTML — the shape a port forces, since Python would own composition.
It doubles as a measuring stick: the twin is what a template renders when no
child component runs, i.e. the engine's own evaluation.

Measured on the 997-doc corpus (2026-09-21), `--reps 120`, minijinja 2.24.0:

    template        Jinja2 us   twin us   MiniJinja us    (twin = this template's own
    Doc                8809.9      15.8           14.7     evaluation, children stubbed
    Base                913.3     125.8          439.5     to {{ childN }})
    NavAccordion         24.8      25.6           90.1
    whole page render               15973 us

Three conclusions, all measured:

1. Template *evaluation* is ~1% of a page render (16 + 126 + 26 us of 16 ms), so
   swapping the engine cannot pay. The cost is running children, emitting the
   ~250 KB page string, and the Python machinery around each render
   (`_extract_slots` over 250 KB, `inject_scope_attr` over 256 KB).
2. The Rust engine measured *slower* through the Python binding — 3.5x on the two
   templates that call Python globals or walk Python attributes (Base, the nav) —
   because every value crosses the FFI per access.
3. The raw source is accepted but wrong: minijinja renders the `<Base .../>`
   component tags as literal text (its delimiters are `{{ }}`), so the component
   lexer extension would have to be replaced, not ported. Even the twin's output
   differs from Jinja2's by one trailing byte.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

THEME = REPO / "themes" / "docs"
TARGETS = ("Base", "Doc", "NavAccordion")
PROBE = '{% for e in entries %}<li><a href="/{{ e.id }}/">{{ e.data.title }}</a></li>{% endfor %}'
# epresso component tags: `<Name ...>`, `<Name .../>`, `</Name>` (uppercase = component).
_JSX = re.compile(
    r"<([A-Z][A-Za-z0-9_.]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*?)(/?)>"
    r"|</([A-Z][A-Za-z0-9_.]*)>"
)


def find_component(name: str) -> Path | None:
    hits = sorted(THEME.rglob(f"{name}.ep"))
    return hits[0] if hits else None


def template_source(site, path: Path) -> str:
    """The exact source Jinja compiles for this component."""
    from epresso.components import _expand_slots
    from epresso.document import parse_document

    doc = parse_document(path.read_text(encoding="utf-8"), "ep")
    body = site._apply_source_transforms(doc.body, kind="component", path=str(path))
    return _expand_slots(body)


def capture(site):
    """Render real routes; return ({name: (template, ctx)}, all templates, page route).

    Templates must be grabbed *during* the render: `_parse_component`'s cache
    does not keep a pre-called object alive for the render to hit.
    """
    import jinja2

    import epresso.components as comp

    named: dict[str, tuple[object, dict]] = {}
    every: dict[int, tuple[object, dict]] = {}
    original_parse, original_render = comp._parse_component, jinja2.Template.render

    def spy_parse(path, environment, site=None):
        parsed = original_parse(path, environment, site)
        stem = Path(path).stem
        if stem in TARGETS:
            named.setdefault(stem, (parsed[6], {}))
        return parsed

    def spy_render(self, *args, **kwargs):
        every.setdefault(id(self), (self, dict(kwargs)))
        for tmpl, ctx in named.values():
            if self is tmpl and not ctx:
                ctx.update(kwargs)
        return original_render(self, *args, **kwargs)

    comp._parse_component = spy_parse
    jinja2.Template.render = spy_render
    page = None
    try:
        pages = [r for r in site.resolve_routes() if r.template_str and not r.redirect_to]
        page = pages[0]
        site.render_route(page)
    finally:
        comp._parse_component = original_parse
        jinja2.Template.render = original_render
    return {n: v for n, v in named.items() if v[1]}, every, page


def timeit(fn, reps: int) -> float:
    fn()  # warm
    t = time.perf_counter()
    for _ in range(reps):
        fn()
    return (time.perf_counter() - t) / reps


def strip_component_tags(source: str) -> tuple[str, int]:
    """Component tags -> `{{ childN }}` (see module doc).

    epresso's `<Card .../>` tags are a Jinja *lexer extension*, not a text
    rewrite, so they survive `_expand_slots` — and MiniJinja, whose delimiters
    are `{{ }}`, would happily render them as literal text. Replacing the tags is
    therefore required for a twin that both engines can run at all.
    """
    counter = [0]

    def sub(m: re.Match[str]) -> str:
        if m.group(4) is not None:  # closing </Name>
            return ""
        n = counter[0]
        counter[0] += 1
        return "{{ child" + str(n) + " }}"

    return _JSX.sub(sub, source), counter[0]


def first_diff(a: str, b: str) -> str:
    """Where two renders first disagree — a byte diff is a porting bug, not noise."""
    for i, (x, y) in enumerate(zip(a, b, strict=False)):
        if x != y:
            lo, hi = max(0, i - 30), i + 30
            return f"@{i}: {a[lo:hi]!r} vs {b[lo:hi]!r}"
    return f"common prefix; lengths {len(a)} vs {len(b)}"


def minijinja_env(env, source: str, children: int):
    mj = importlib.import_module("minijinja")
    built = mj.Environment(templates={"t": source})
    for name, fn in getattr(env, "filters", {}).items():
        try:
            built.add_filter(name, fn)
        except Exception:  # noqa: BLE001 - engine-side rejection is data, not failure
            pass
    for name, value in getattr(env, "globals", {}).items():
        try:
            built.add_global(name, value)
        except Exception:  # noqa: BLE001
            pass
    for n in range(children):
        built.add_global(f"child{n}", "")
    return built


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reps", type=int, default=150)
    ap.add_argument("--source", type=Path, default=REPO / "docs", help="Markdown corpus to render")
    args = ap.parse_args(argv)

    from epresso.docsgen import auto_docs_project
    from epresso.site import Site

    tmp = auto_docs_project(args.source.resolve(), 4321, THEME)
    site = Site.load(tmp)
    named, every, page = capture(site)
    if not named:
        print("no components captured — nothing to benchmark")
        return 1
    have_mj = importlib.util.find_spec("minijinja") is not None

    print(f"engine_bench  source={args.source}  docs={len(site.store.get_collection('docs'))}  reps={args.reps}")
    print(f"{'template':14s} {'ctx':>4s} {'Jinja2 us':>10s} {'twin us':>9s} {'MiniJinja':>10s}  note")
    for name, (tmpl, ctx) in named.items():
        us_j = timeit(lambda tmpl=tmpl, ctx=ctx: tmpl.render(**ctx), args.reps) * 1e6
        # The twin stubs every child component to `{{ childN }}` with empty HTML,
        # so it measures this template's own evaluation + the Python machinery
        # `_render_epresso_component` runs for it — not the children.
        twin, kids = strip_component_tags(template_source(site, find_component(name)))
        tw = site.env.from_string(twin)
        twin_ctx = {**ctx, **{f"child{i}": "" for i in range(kids)}}
        us_t = f"{timeit(lambda tw=tw, twin_ctx=twin_ctx: tw.render(**twin_ctx), args.reps) * 1e6:.1f}" if kids else "-"
        note, us_m = "", "-"
        if have_mj:
            try:
                built = minijinja_env(site.env, twin, kids)
                mj_out = built.render_template("t", **twin_ctx)

                def render_mj(built=built, twin_ctx=twin_ctx):
                    return built.render_template("t", **twin_ctx)

                us_m = f"{timeit(render_mj, args.reps) * 1e6:.1f}"
                jinja_out = str(tw.render(**twin_ctx))
                mj_str = str(mj_out)
                note = "twin" if mj_str == jinja_out else f"twin; OUTPUT DIFFERS — {first_diff(jinja_out, mj_str)}"
                try:
                    raw = minijinja_env(site.env, template_source(site, find_component(name)), 0)
                    raw_out = str(raw.render_template("t", **ctx))
                    real_out = str(tmpl.render(**ctx))
                    note += (
                        "; raw accepted, renders JSX literally"
                        if raw_out != real_out
                        else "; raw source equivalent (!)"
                    )
                except Exception as exc:  # noqa: BLE001
                    note += f"; raw source rejected: {type(exc).__name__}"
            except Exception as exc:  # noqa: BLE001
                note = f"failed: {type(exc).__name__}: {exc}"
        else:
            note = "SKIP: pip install minijinja"
        print(f"{name:14s} {len(ctx):4d} {us_j:10.1f} {us_t:>9s} {us_m:>10s}  {note}")

    # The per-template times above are inclusive: rendering `Doc` in isolation
    # re-runs `Base` (its `{% component %}` child), so they must not be summed.
    page_us = timeit(lambda: site.render_route(page), 20) * 1e6
    print(f"\npage render: {page_us:.0f} us  ({len(every)} distinct templates)")
    print("  (the isolated rows above include child components — not addable)")

    docs = site.store.get_collection("docs")
    probe = max(args.reps // 4, 1)
    us_probe = timeit(lambda: site.env.from_string(PROBE).render(entries=docs), probe) * 1e6
    print(f"\nmarshalling probe ({len(docs)} real entries, .id/.data.title per item): Jinja2 {us_probe:.1f} us")
    if not have_mj:
        print("\nMiniJinja not installed in this interpreter; the Jinja2 numbers above are real.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
