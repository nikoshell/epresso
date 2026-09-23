#!/usr/bin/env python3
"""epresso render-pipeline benchmarks: phase microbench + page-scale sweep.

    python bench/run.py phases                     # phase x cold/warm, per fixture
    python bench/run.py scale --sizes 1,10,100     # synthetic site at each page count
    python bench/run.py all --json bench/results.json

`phases` isolates each pipeline stage by calling that stage's own function
(Markdown parse vs render vs Pygments, component expansion, Jinja, minify, file
write), so a slow row points at one module. `scale` measures the real
`Site.load` + `Site.build` path at 1..10,000 pages and splits it with
`BuildResult.perf`.

Terminology:
  cold  first invocation in a fresh process — no warm caches, cold page cache.
  warm  median of the remaining runs in the same process (caches populated).

Cold is a single sample (and therefore noisy); warm is the number to trust.
Nothing here is committed as a gate — `scripts/bench.py` remains the CI
regression gate. This suite is for finding and comparing costs.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from epresso.components import _render_component  # noqa: E402
from epresso.config import Config  # noqa: E402
from epresso.document import parse_document, split_frontmatter  # noqa: E402
from epresso.markdown import (  # noqa: E402
    _pygments_highlight,
    _renderer,
    component_placeholder,
    render_markdown,
)
from epresso.minify import minify_html  # noqa: E402
from epresso.scoped import inject_scope_attr  # noqa: E402
from epresso.site import Site  # noqa: E402

BENCH = Path(__file__).resolve().parent
FIXTURES = ("small", "medium", "large", "code-heavy", "components", "docs")
DEFAULT_SIZES = (1, 10, 100)
ALL_SIZES = (1, 10, 100, 1000, 10000)

# A fixed snippet for the isolated Pygments rows, so those rows are comparable
# across fixtures instead of depending on whichever fence a fixture happens to
# contain first.
PYGMENTS_SNIPPET = (
    "from pathlib import Path\n\n\n"
    "def walk(root: Path, suffix: str = '.md') -> list[Path]:\n"
    '    """Every matching file under root, sorted for determinism."""\n'
    "    return sorted(p for p in root.rglob('*') if p.is_file() and p.suffix == suffix)\n"
    "\n\n"
    "class Store:\n"
    "    def __init__(self) -> None:\n"
    "        self._by_name: dict[str, list[object]] = {}\n"
    "\n"
    "    def register(self, name: str, value: object) -> None:\n"
    "        self._by_name.setdefault(name, []).append(value)\n"
)

JINJA_TEMPLATE = (
    "<ul>"
    "{% for item in items %}"
    '<li class="{{ item.kind }}" data-i="{{ loop.index }}">'
    "{% if item.kind == 'primary' %}<strong>{{ item.name }}</strong>"
    "{% else %}{{ item.name }}{% endif %}</li>"
    "{% endfor %}"
    "</ul>"
)

CARD_EP = """\
---
from pydantic import BaseModel


class Props(BaseModel):
    title: str = ""
    variant: str = "default"
---
<section class="card card-{{ props.variant }}">
<h2>{{ props.title }}</h2>
<slot/>
</section>
<style>.card{border:1px solid #ccc;padding:1rem}.card h2{margin:0 0 .5rem}</style>
"""

BUTTON_EP = """\
---
from pydantic import BaseModel


class Props(BaseModel):
    url: str = "/"
    variant: str = "default"
---
<a class="btn btn-{{ props.variant }}" href="{{ url(props.url) }}"><slot/></a>
"""

BASE_EP = """\
---
---
<!doctype html><html lang="en"><head><meta charset="utf-8">\
<title>{{ props.title }}</title></head><body><main><slot/></main></body></html>
"""


@dataclass
class Fixture:
    """One fixture, pre-parsed, with the bits each phase needs."""

    name: str
    path: Path
    source: str
    body: str
    tokens: list
    html: str
    size: int


@dataclass
class Harness:
    """Shared objects: a real Site (config + bound Jinja env) and one MarkdownIt."""

    site: Site
    cfg: Config
    env: object
    md: object
    tmp: Path


def _workspace() -> Harness:
    """A throwaway site with two components and a layout, for the Jinja rows.

    Uses ``Site.load`` so the environment is bound exactly as a build binds it
    (curated globals, ``site``, ``_render_session``) and component resolution
    works through the real searchpath.
    """
    tmp = Path(tempfile.mkdtemp(prefix="epresso-bench-"))
    (tmp / "components").mkdir(parents=True)
    (tmp / "layouts").mkdir(parents=True)
    (tmp / "pages").mkdir(parents=True)
    (tmp / "components" / "Card.ep").write_text(CARD_EP, encoding="utf-8")
    (tmp / "components" / "Button.ep").write_text(BUTTON_EP, encoding="utf-8")
    (tmp / "layouts" / "Base.ep").write_text(BASE_EP, encoding="utf-8")
    (tmp / "site.toml").write_text(
        '[site]\nname = "bench"\n[markdown]\ncomponents = ["Card", "Button"]\n'
        'code_component = "Highlight"\ncode_components = { tree = "Tree" }\n',
        encoding="utf-8",
    )
    site = Site.load(tmp)
    md = _renderer(site.config.markdown, ("Card", "Button"), component_placeholder)
    return Harness(site=site, cfg=site.config, env=site.env, md=md, tmp=tmp)


def _load_fixture(name: str, h: Harness) -> Fixture:
    path = BENCH / f"{name}.md"
    source = path.read_text(encoding="utf-8")
    doc = parse_document(source, "markdown")
    body = doc.body
    return Fixture(
        name=name,
        path=path,
        source=source,
        body=body,
        tokens=h.md.parse(body),
        html=h.md.render(body),
        size=path.stat().st_size,
    )


def _measure(fn, runs: int) -> tuple[float, float]:
    """Return ``(cold, warm)`` seconds: first call, then median of ``runs``."""
    t0 = time.perf_counter()
    fn()
    cold = time.perf_counter() - t0
    samples = []
    for _ in range(max(1, runs)):
        t0 = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - t0)
    return cold, statistics.median(samples)


def _phases(h: Harness, fx: Fixture, out_file: Path) -> list[tuple[str, object]]:
    """The phase registry for one fixture: ``(name, callable)``."""
    items = [{"kind": "primary" if i % 3 == 0 else "muted", "name": f"Item {i}"} for i in range(20)]
    tmpl = h.env.from_string(JINJA_TEMPLATE)

    return [
        ("file loading", lambda: fx.path.read_bytes()),
        ("frontmatter (YAML)", lambda: parse_document(fx.source, "markdown")),
        ("Markdown parsing", lambda: h.md.parse(fx.body)),
        ("Markdown rendering", lambda: h.md.renderer.render(fx.tokens, h.md.options, {})),
        ("Pygments (plain)", lambda: _pygments_highlight(PYGMENTS_SNIPPET, "python", "")),
        (
            "Pygments (code component)",
            lambda: _pygments_highlight(PYGMENTS_SNIPPET, "python", "", "Highlight", {}),
        ),
        (
            "component expansion",
            lambda: _render_component(h.env, "Card", "<p>child</p>", {"title": "Bench", "variant": "default"}),
        ),
        ("Jinja (compile + render)", lambda: h.env.from_string(JINJA_TEMPLATE).render(items=items)),
        ("Jinja (warm render)", lambda: tmpl.render(items=items)),
        (
            "HTML postprocessing",
            lambda: inject_scope_attr(minify_html(fx.html), "deadbeef"),
        ),
        ("filesystem output", lambda: out_file.write_text(fx.html, encoding="utf-8")),
        (
            "total (render_markdown)",
            lambda: render_markdown(
                fx.body,
                h.cfg.markdown,
                image_base="/content/bench/",
                component_names=("Card", "Button"),
                component_renderer=component_placeholder,
            ),
        ),
    ]


def cmd_phases(args: argparse.Namespace) -> dict:
    h = _workspace()
    out_file = h.tmp / "out.html"
    names = [n for n in FIXTURES if args.fixture in (None, n)]
    results: dict[str, dict] = {}

    for name in names:
        fx = _load_fixture(name, h)
        rows = []
        for phase, fn in _phases(h, fx, out_file):
            cold, warm = _measure(fn, args.runs)
            rows.append((phase, cold, warm))
        results[name] = {
            "bytes": fx.size,
            "phases": {p: {"cold_s": c, "warm_s": w} for p, c, w in rows},
        }
        _print_phase_table(name, fx.size, rows)

    return {"phases": results}


def _print_phase_table(name: str, size: int, rows: list[tuple[str, float, float]]) -> None:
    print(f"\n── {name}  ({size / 1024:.1f} KB) " + "─" * 40)
    print(f"  {'phase':<28}{'cold ms':>10}{'warm ms':>10}{'cold/warm':>11}")
    for phase, cold, warm in rows:
        ratio = (cold / warm) if warm else 0.0
        print(f"  {phase:<28}{cold * 1000:>10.3f}{warm * 1000:>10.3f}{ratio:>10.2f}x")


# ── scale sweep ──────────────────────────────────────────────────────────────

SCALE_FIXTURE = {"docs": "docs", "code": "code-heavy", "ep": None}


def _make_site(root: Path, n: int, shape: str) -> None:
    """Write ``n`` pages of ``shape`` under ``root`` (a fresh temp project)."""
    (root / "pages").mkdir(parents=True, exist_ok=True)
    (root / "site.toml").write_text(
        '[site]\nname = "bench"\nurl = "http://localhost:8000"\n'
        '[build]\ntrailing_slash = "always"\n',
        encoding="utf-8",
    )
    if shape == "ep":
        (root / "layouts").mkdir(parents=True, exist_ok=True)
        (root / "components").mkdir(parents=True, exist_ok=True)
        (root / "layouts" / "Base.ep").write_text(BASE_EP, encoding="utf-8")
        (root / "components" / "Card.ep").write_text(CARD_EP, encoding="utf-8")
        for i in range(n):
            (root / "pages" / f"p{i:05d}.ep").write_text(
                f'---\ntitle: "Page {i}"\n---\n<Base title={{props.title}}>\n<h1>Page {i}</h1>\n'
                f'<Card title="Card {i}"><p>Body copy for page {i}.</p></Card>\n</Base>\n',
                encoding="utf-8",
            )
        return

    fixture = BENCH / f"{SCALE_FIXTURE[shape]}.md"
    _, body = split_frontmatter(fixture.read_text(encoding="utf-8"))
    for i in range(n):
        page = f'---\ntitle: "Page {i}"\ndescription: bench page {i}\n---\n\n{body}\n'
        (root / "pages" / f"p{i:05d}.md").write_text(page, encoding="utf-8")


def _build_once(root: Path, *, clean: bool) -> tuple[float, dict, int]:
    """``Site.load`` + ``Site.build``; returns ``(seconds, perf, pages)``."""
    t0 = time.perf_counter()
    site = Site.load(root)
    result = site.build(clean=clean)
    total = time.perf_counter() - t0
    return total, dict(result.perf), len(result.pages) + len(result.endpoints)


def _summary_markdown(scale: dict[str, list]) -> str:
    """A GitHub-Actions job summary for a scale run: a table + a Mermaid pie.

    GitHub renders Mermaid in step summaries but pins an older Mermaid, where
    ``xychart-beta`` does not render — so the phase breakdown uses a ``pie``
    (supported everywhere) rather than a line/bar chart.
    """
    order = ["collections", "content", "setup", "render", "assets", "images_bundles", "outputs"]
    lines = ["## Render benchmark", ""]
    for shape, rows in scale.items():
        if not rows:
            continue
        present = [k for k in order if any(k in r["perf"] for r in rows)]
        lines.append(f"### `{shape}` pages")
        lines.append("")
        header = ["pages", "cold s", "warm s"] + [f"{k} ms" for k in present]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "---|" * len(header))
        for r in rows:
            perf = r["perf"]
            cells = [str(r["pages"]), f"{r['cold_s']:.3f}", f"{r['warm_s']:.3f}"]
            cells += [f"{perf.get(k, 0) * 1000:.1f}" for k in present]
            lines.append("| " + " | ".join(cells) + " |")

        biggest = rows[-1]
        slices = sorted(((k, v * 1000) for k, v in biggest["perf"].items() if v > 0), key=lambda kv: -kv[1])
        if slices:
            lines += [
                "",
                "```mermaid",
                "pie",
                f'    title Build phase share — {shape}, {biggest["pages"]} pages (cold)',
                *[f'    "{k}" : {ms:.1f}' for k, ms in slices],
                "```",
            ]
        lines.append("")
    return "\n".join(lines) + "\n"


def cmd_scale(args: argparse.Namespace) -> dict:
    shapes = [args.shape] if args.shape != "all" else ["docs", "code", "ep"]
    if args.sizes == "all":
        sizes = list(ALL_SIZES)
    else:
        sizes = [int(s) for s in args.sizes.split(",") if s.strip()]
    results: dict[str, list] = {}

    for shape in shapes:
        print(f"\n══ scale: {shape} pages " + "═" * 40)
        print(
            f"  {'pages':>7}{'cold s':>10}{'warm s':>10}{'collections':>12}"
            f"{'content':>10}{'render':>9}{'outputs':>9}{'total cold':>11}"
        )
        rows = []
        for n in sizes:
            with tempfile.TemporaryDirectory(prefix=f"epresso-scale-{shape}-") as d:
                root = Path(d)
                _make_site(root, n, shape)
                cold, cold_perf, pages = _build_once(root, clean=True)
                warm, _, _ = _build_once(root, clean=False)
            row = {"pages": n, "cold_s": cold, "warm_s": warm, "perf": cold_perf}
            rows.append(row)
            print(
                f"  {n:>7}{cold:>10.3f}{warm:>10.3f}"
                f"{cold_perf.get('collections', 0):>12.3f}"
                f"{cold_perf.get('content', 0):>10.3f}"
                f"{cold_perf.get('render', 0):>9.3f}"
                f"{cold_perf.get('outputs', 0):>9.3f}"
                f"{cold:>11.3f}"
            )
            if n >= 1000 and pages == 0:
                print("  ⚠️  built 0 pages — the generator or a path is wrong")
        results[shape] = rows

    if getattr(args, "summary", None):
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(_summary_markdown(results), encoding="utf-8")
        print(f"\nwrote {args.summary}")
    return {"scale": results}


def cmd_all(args: argparse.Namespace) -> dict:
    out = cmd_phases(args)
    out.update(cmd_scale(args))
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--runs", type=int, default=5, help="warm samples per phase (default 5)")
        sp.add_argument("--json", type=Path, help="write raw results to this JSON file")

    pp = sub.add_parser("phases", help="phase microbench per fixture")
    pp.add_argument("--fixture", choices=FIXTURES, help="only this fixture (default: all)")
    common(pp)

    ps = sub.add_parser("scale", help="synthetic site build at each page count")
    ps.add_argument("--sizes", default=",".join(map(str, DEFAULT_SIZES)), help="comma list, or 'all' for 1..10000")
    ps.add_argument("--shape", default="docs", choices=["docs", "code", "ep", "all"])
    ps.add_argument("--summary", type=Path, help="write a markdown summary (table + Mermaid pie) to this file")
    common(ps)

    pa = sub.add_parser("all", help="phases + scale")
    pa.add_argument("--fixture", choices=FIXTURES)
    pa.add_argument("--sizes", default=",".join(map(str, DEFAULT_SIZES)))
    pa.add_argument("--shape", default="docs", choices=["docs", "code", "ep", "all"])
    pa.add_argument("--summary", type=Path, help="write a markdown summary (table + Mermaid pie) to this file")
    common(pa)

    args = p.parse_args(argv)
    dispatch = {"phases": cmd_phases, "scale": cmd_scale, "all": cmd_all}
    results = dispatch[args.cmd](args)

    if getattr(args, "json", None):
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
