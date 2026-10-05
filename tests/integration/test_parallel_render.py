"""Parallel (forked) rendering produces exactly the serial output."""

import multiprocessing as mp
import shutil
from pathlib import Path

import pytest

from epresso import site as site_mod
from epresso.config import load_config
from epresso.site import Site

THEME = Path(__file__).resolve().parents[2] / "themes" / "docs"

pytestmark = pytest.mark.skipif("fork" not in mp.get_all_start_methods(), reason="needs fork()")


def _tree(d: Path) -> dict[str, bytes]:
    return {str(p.relative_to(d)): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file()}


def test_parallel_matches_serial(tmp_path, monkeypatch):
    proj = tmp_path / "site"
    shutil.copytree(THEME, proj, ignore=shutil.ignore_patterns("dist", ".cache", "__pycache__"))
    monkeypatch.setenv("EPRESSO_JOBS", "1")
    Site(load_config(proj)).build()
    serial = _tree(proj / "dist")

    monkeypatch.setattr(site_mod, "PARALLEL_MIN_ROUTES", 1)
    monkeypatch.setenv("EPRESSO_JOBS", "4")
    assert site_mod._build_jobs(load_config(proj), 100) > 1
    Site(load_config(proj)).build()
    parallel = _tree(proj / "dist")
    assert sorted(set(serial) ^ set(parallel)) == []
    assert [k for k in serial if serial[k] != parallel[k]] == []


def test_worker_error_surfaces_from_parent(tmp_path, monkeypatch):
    proj = tmp_path / "site"
    (proj / "pages").mkdir(parents=True)
    (proj / "site.toml").write_text('[site]\nname = "x"\n', encoding="utf-8")
    for i in range(20):
        (proj / "pages" / f"p{i}.ep").write_text("<p>{{ 1 }}</p>\n", encoding="utf-8")
    (proj / "pages" / "bad.ep").write_text("<p>{{ nope() }}</p>\n", encoding="utf-8")
    monkeypatch.setattr(site_mod, "PARALLEL_MIN_ROUTES", 1)
    monkeypatch.setenv("EPRESSO_JOBS", "2")
    with pytest.raises(Exception, match="nope"):
        Site(load_config(proj)).build()
