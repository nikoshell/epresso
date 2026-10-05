"""Page reuse stays on with html-transform plugins, and reused output == fresh output."""

import shutil
from pathlib import Path

from epresso.config import load_config
from epresso.site import Site

THEME = Path(__file__).resolve().parents[2] / "themes" / "docs"


def _tree(d: Path) -> dict[str, bytes]:
    return {str(p.relative_to(d)): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file()}


def test_reused_build_matches_fresh(tmp_path):
    proj = tmp_path / "site"
    shutil.copytree(THEME, proj, ignore=shutil.ignore_patterns("dist", ".cache", "__pycache__"))
    fresh = Site(load_config(proj)).build()
    assert fresh.skipped == 0
    first = _tree(proj / "dist")
    again = Site(load_config(proj)).build(keep_cache=True)
    assert again.skipped == len(again.pages) + len(again.endpoints)  # every route reused
    second = _tree(proj / "dist")
    assert sorted(set(first) ^ set(second)) == []
    changed = [k for k in first if first[k] != second[k]]
    assert not changed, changed[:5]



def test_body_edit_rerenders_one_page_title_edit_rerenders_nav(tmp_path):
    from epresso.docsgen import auto_docs_project

    src = tmp_path / "proj"
    (src / "docs").mkdir(parents=True)
    (src / "README.md").write_text("# Home\n\nhi\n", encoding="utf-8")
    for i in range(6):
        (src / "docs" / f"p{i}.md").write_text(f"# Page {i}\n\nbody {i}\n", encoding="utf-8")

    def build():
        proj = auto_docs_project(src, port=9999)
        return proj, Site(load_config(proj)).build(keep_cache=True)

    _, first = build()
    routes = len(first.pages) + len(first.endpoints)
    _, warm = build()
    assert warm.skipped == routes

    (src / "docs" / "p2.md").write_text("# Page 2\n\nnew body\n", encoding="utf-8")
    proj, edit = build()
    assert routes - edit.skipped <= 2  # the page + its .md endpoint, not every page
    assert "new body" in (proj / "dist" / "p2" / "index.html").read_text(encoding="utf-8")

    (src / "docs" / "p2.md").write_text("# Renamed Page\n\nnew body\n", encoding="utf-8")
    proj, retitle = build()
    assert retitle.skipped < routes // 2  # the sidebar changed everywhere
    assert "Renamed Page" in (proj / "dist" / "p4" / "index.html").read_text(encoding="utf-8")
