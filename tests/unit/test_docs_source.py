"""The docs-source resolver (epresso.docs_source)."""

from pathlib import Path

from epresso.docs_source import DEFAULT_DOCS_DIR, resolve_docs_source


def test_default_base_is_root_docs_dir(tmp_path: Path):
    src = resolve_docs_source(tmp_path)
    assert src.docs_dir == DEFAULT_DOCS_DIR
    assert src.base == tmp_path / "docs"
    assert src.repo_root is None  # not a git repo at root


def test_docs_base_override_wins(tmp_path: Path):
    override = tmp_path / "copied"
    override.mkdir()
    src = resolve_docs_source(tmp_path, docs_dir="site", docs_base=override)
    assert src.base == override
    assert src.docs_dir == "site"


def test_repo_root_only_when_root_is_a_git_repo(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    src = resolve_docs_source(tmp_path)
    assert src.repo_root == tmp_path


def test_no_parent_walk_for_repo(tmp_path: Path):
    # repo is at a parent; root itself has no .git -> not a repo here
    parent = tmp_path / "parent"
    child = parent / "site"
    (parent / ".git").mkdir(parents=True)
    child.mkdir()
    src = resolve_docs_source(child)
    assert src.repo_root is None
