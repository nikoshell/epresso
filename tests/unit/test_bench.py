"""Bench harness logic — the gate math, without running real builds."""

import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location("bench", Path(__file__).resolve().parents[2] / "scripts" / "bench.py")
assert _SPEC and _SPEC.loader
bench = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(bench)


def test_compare_flags_slowdown_past_threshold():
    ok, delta = bench.compare(15.0, 11.0, 0.25)
    assert ok is False
    assert delta == pytest.approx(0.3636, abs=1e-4)


def test_compare_allows_slowdown_within_threshold():
    ok, delta = bench.compare(11.5, 11.0, 0.25)
    assert ok is True
    assert delta == pytest.approx(0.0455, abs=1e-4)


def test_compare_treats_speedup_as_ok():
    ok, delta = bench.compare(8.0, 11.0, 0.25)
    assert ok is True
    assert delta < 0


def test_pages_built_reads_the_cli_success_line():
    line = "[cli] ✅ Built 38 pages, 36 endpoints (0 cached) from 1 collections (51 entries) in 2.51s"
    assert bench._pages_built(line) == 38


def test_pages_built_is_negative_when_the_line_is_absent():
    assert bench._pages_built("some other output") == -1


class _Completed:
    def __init__(self, returncode: int, stdout: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


def test_build_seconds_rejects_a_zero_page_build(monkeypatch, tmp_path):
    """A wrong --theme path is a silent CLI success, so the harness must catch it."""
    empty = "[cli] ✅ Built 0 pages, 0 endpoints (0 cached) from 0 collections (0 entries) in 0.00s"
    monkeypatch.setattr(bench.subprocess, "run", lambda *a, **k: _Completed(0, empty))
    with pytest.raises(SystemExit) as exc:
        bench.build_seconds("themes/typo", runs=1)
    assert exc.value.code == 2


def test_build_seconds_rejects_a_failing_build(monkeypatch):
    monkeypatch.setattr(bench.subprocess, "run", lambda *a, **k: _Completed(1, ""))
    with pytest.raises(SystemExit) as exc:
        bench.build_seconds("themes/docs", runs=1)
    assert exc.value.code == 2


def test_build_seconds_returns_best_and_median(monkeypatch):
    out = "[cli] ✅ Built 38 pages, 36 endpoints (0 cached) from 1 collections (51 entries) in 2.51s"
    monkeypatch.setattr(bench.subprocess, "run", lambda *a, **k: _Completed(0, out))
    ticks = iter([0.0, 3.0, 10.0, 12.0, 20.0, 22.0])
    monkeypatch.setattr(bench.time, "perf_counter", lambda: next(ticks))
    best, median = bench.build_seconds("themes/docs", runs=3)
    assert (best, median) == (2.0, 2.0)
