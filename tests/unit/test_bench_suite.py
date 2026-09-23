"""bench/run.py — harness smoke tests.

Deliberately small: one phase registry pass and one page generation, not a
sweep. The suite itself is a measurement tool; these tests only guard that it
still runs and that its fixtures parse.
"""

import importlib.util
import sys
from pathlib import Path

_PATH = Path(__file__).resolve().parents[2] / "bench" / "run.py"
_SPEC = importlib.util.spec_from_file_location("bench_run", _PATH)
assert _SPEC and _SPEC.loader
bench = importlib.util.module_from_spec(_SPEC)
# Register before exec: bench/run.py uses @dataclass, which reads
# sys.modules[cls.__module__] while the class body is created.
sys.modules[_SPEC.name] = bench
_SPEC.loader.exec_module(bench)


def test_measure_returns_cold_and_warm_and_samples():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1

    cold, warm = bench._measure(fn, 3)
    assert cold >= 0.0 and warm >= 0.0
    assert calls["n"] == 4  # one cold + three warm


def test_every_fixture_loads_parses_and_renders():
    harness = bench._workspace()
    for name in bench.FIXTURES:
        fx = bench._load_fixture(name, harness)
        assert fx.body, name
        assert fx.tokens, name
        assert fx.html, name
        assert fx.size > 0, name


def test_phase_registry_runs_for_one_fixture():
    harness = bench._workspace()
    fx = bench._load_fixture("small", harness)
    out_file = harness.tmp / "out.html"
    phases = bench._phases(harness, fx, out_file)
    names = [p for p, _fn in phases]
    assert "Markdown parsing" in names
    assert "Markdown rendering" in names
    for _name, fn in phases:
        fn()  # every phase must be callable without error


def test_make_site_writes_n_pages(tmp_path):
    bench._make_site(tmp_path, 7, "docs")
    assert len(list((tmp_path / "pages").glob("*.md"))) == 7
    assert (tmp_path / "site.toml").is_file()


def test_make_site_ep_shape_writes_layout_and_components(tmp_path):
    bench._make_site(tmp_path, 3, "ep")
    assert len(list((tmp_path / "pages").glob("*.ep"))) == 3
    assert (tmp_path / "layouts" / "Base.ep").is_file()
    assert (tmp_path / "components" / "Card.ep").is_file()


def test_summary_has_table_and_mermaid_pie():
    results = {
        "docs": [
            {
                "pages": 200,
                "cold_s": 0.5,
                "warm_s": 0.03,
                "perf": {"render": 0.4, "outputs": 0.02, "collections": 0.0},
            }
        ]
    }
    md = bench._summary_markdown(results)
    assert "| pages | cold s | warm s |" in md
    assert "```mermaid" in md
    assert "pie" in md
    assert "render" in md
    # a zero phase must not become a zero-width pie slice
    assert '"collections"' not in md
