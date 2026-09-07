"""Tests for the reusable Markdown docs loader (epresso.content.docs)."""

from pathlib import Path

from pydantic import BaseModel

from epresso.content.docs import DocsLoader
from epresso.content.store import Collection, ContentStore


class Doc(BaseModel):
    title: str
    description: str = ""

MD = {
    "README.md": "# Overview\n\nhome\n",
    "basics/components.md": "# Components\n\n## API\n\nbody\n",
    "basics/layouts.md": "# Layouts\n\nbody\n",
    "develop-and-build/index.md": "# Develop and build\n\nbody\n",
    "develop-and-build/cli.md": "# CLI\n\nbody\n",
    "editor-setup/index.md": "# Editor setup\n\nbody\n",
}


def _write(root: Path) -> None:
    for rel, text in MD.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def _load(root: Path):
    store = ContentStore()
    col = Collection("docs", schema=Doc)
    store.register(col)
    DocsLoader(root, "**/*.{md,markdown}", "docs").load(store, col)
    return {e.id: e for e in col.all()}


def test_authored_data_is_only_frontmatter(tmp_path: Path):
    _write(tmp_path)
    docs = _load(tmp_path)
    # data holds only authored fields; the rest is derived in computed.
    assert docs["basics/components"].data.model_dump() == {
        "title": "Components",
        "description": "",
    }
    assert "group_path" not in docs["basics/components"].data.model_dump()


def test_computed_has_derived_fields(tmp_path: Path):
    _write(tmp_path)
    c = _load(tmp_path)["basics/components"].computed
    assert c["group_path"] == ["basics"]
    assert c["order"] == 1  # 0 is the root overview
    assert any(h["text"] == "API" for h in c["headings"])
    # hub id drops the index filename: develop-and-build/index.md -> "develop-and-build".
    assert _load(tmp_path)["develop-and-build"].computed["is_hub"]


def test_lone_index_flattens(tmp_path: Path):
    """A <dir>/index.md alone collapses to a flat root-level page (like <dir>.md)."""
    _write(tmp_path)
    es = _load(tmp_path)["editor-setup"]
    # it stays a hub (is_hub) but is dropped to root level (no dir to head).
    assert es.computed["group_path"] == []
    assert es.computed["is_hub"]


def test_source_is_repo_relative_even_from_a_copied_base(tmp_path: Path):
    """The GitHub 'edit this page' source must stay repo-root relative (docs/…)
    even when the docs are read from a copied base — the ``epresso docs --theme``
    preview flow copies a repo's docs into a temp dir distinct from the repo's
    own docs dir (previously this dropped the ``docs/`` prefix)."""
    import shutil

    repo_docs = tmp_path / "repo" / "docs"
    (repo_docs / "basics").mkdir(parents=True)
    (repo_docs / "basics" / "components.md").write_text("# Components\n\nbody\n", encoding="utf-8")
    # copy into a separate base, as auto_docs_project does
    copy_base = tmp_path / "copy" / "docs"
    shutil.copytree(repo_docs, copy_base)

    store = ContentStore()
    col = Collection("docs", schema=Doc)
    store.register(col)
    DocsLoader(copy_base, "**/*.{md,markdown}", "docs").load(store, col)
    entry = {e.id: e for e in col.all()}["basics/components"]
    assert entry.computed["source"] == "docs/basics/components.md"


def test_source_has_docs_prefix_when_reading_repo_docs_directly(tmp_path: Path):
    _write(tmp_path / "docs")
    store = ContentStore()
    col = Collection("docs", schema=Doc)
    store.register(col)
    DocsLoader(tmp_path / "docs", "**/*.{md,markdown}", "docs").load(store, col)
    docs = {e.id: e for e in col.all()}
    assert docs["basics/components"].computed["source"] == "docs/basics/components.md"


def test_prev_next_loop_and_order(tmp_path: Path):
    _write(tmp_path)
    entries = _load(tmp_path)
    real = [e for e in entries.values() if e.id != ""]
    real.sort(key=lambda e: e.computed["order"])
    # nav loops: last -> first, and prev/next carry ready hrefs.
    assert real[-1].computed["next"]["url"] == f"/{real[0].id}/"
    # order is a strict sequence.
    assert [e.computed["order"] for e in real] == sorted(e.computed["order"] for e in real)


def _put(root: Path, rel: str, text: str) -> None:
    q = root / rel
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_text(text, encoding="utf-8")


def _ordered_ids(docs: dict) -> list[str]:
    real = [e for e in docs.values() if e.id != ""]
    real.sort(key=lambda e: e.computed["order"])
    return [e.id for e in real]


def test_curated_order_by_frontmatter_and_hub(tmp_path: Path):
    # red has an index hub (order 1) so its category sorts first; within red the
    # hub leads, then pages by authored order (alpha order 1, beta order 2).
    # blue has no index -> default order 1000 (sorts after red); pages by order.
    _put(tmp_path, "README.md", "# Home\n\nhome\n")
    _put(tmp_path, "red/index.md", "---\ntitle: Red\norder: 1\n---\n# Red\n\nred\n")
    _put(tmp_path, "red/beta.md", "---\ntitle: Beta\norder: 2\n---\n# Beta\n\nbeta\n")
    _put(tmp_path, "red/alpha.md", "---\ntitle: Alpha\norder: 1\n---\n# Alpha\n\nalpha\n")
    _put(tmp_path, "blue/one.md", "---\ntitle: One\norder: 2\n---\n# One\n\none\n")
    _put(tmp_path, "blue/two.md", "---\ntitle: Two\n---\n# Two\n\ntwo\n")
    ids = _ordered_ids(_load(tmp_path))
    assert ids == ["red", "red/alpha", "red/beta", "blue/one", "blue/two"]


def test_unordered_categories_fall_back_to_default_then_alpha(tmp_path: Path):
    _put(tmp_path, "README.md", "# Home\n\nhome\n")
    _put(tmp_path, "zed/x.md", "---\ntitle: X\n---\n# X\n\nx\n")      # no hub -> default 1000
    _put(tmp_path, "abc/y.md", "---\ntitle: Y\n---\n# Y\n\ny\n")      # no hub -> default 1000
    ids = _ordered_ids(_load(tmp_path))
    # both default 1000 -> alphabetical by dir name
    assert ids == ["abc/y", "zed/x"]
