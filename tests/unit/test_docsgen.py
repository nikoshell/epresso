"""Unit tests for the docs-scaffolding helpers (epresso.docsgen)."""

import shutil
import subprocess
from pathlib import Path

import pytest

from epresso.docsgen import (
    auto_docs_project,
    is_repo_dir,
    normalize_repo_url,
    patch_site_toml,
    repo_default_branch,
)


def _write(root: Path, rel: str, content: str = "") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_normalize_repo_url():
    assert normalize_repo_url("git@github.com:a/b.git") == "https://github.com/a/b"
    assert normalize_repo_url("https://github.com/a/b.git") == "https://github.com/a/b"
    assert normalize_repo_url("git://github.com/a/b") == "https://github.com/a/b"
    assert normalize_repo_url(" https://github.com/a/b ") == "https://github.com/a/b"


def test_is_repo_dir_detects_git(tmp_path):
    assert not is_repo_dir(tmp_path)
    (tmp_path / ".git").mkdir()
    assert is_repo_dir(tmp_path)


def test_auto_docs_project_defaults_to_bundled_docs_theme(tmp_path):
    # no theme passed → the bundled themes/docs theme is used, and the bare
    # markdown source is injected as its content/docs collection.
    _write(tmp_path, "intro.md", "# Intro\n")
    proj = auto_docs_project(tmp_path, port=9999)
    assert (proj / "site.toml").exists()
    assert (proj / "components").exists()  # the docs theme was copied in
    assert (proj / "content" / "docs" / "intro.md").exists()  # source injected


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_patch_site_toml_uses_source_repo_repository_and_branch(tmp_path):
    # the source repo: origin remote + recorded default branch (dev)
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "symbolic-ref", "HEAD", "refs/heads/dev")
    _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/dev")
    _git(repo, "remote", "add", "origin", "https://github.com/pwndbg/pwndbg.git")

    # a copied theme whose site.toml points at its own repo/main (the bug: these
    # should be overridden with the source repo's origin + default branch)
    dst = tmp_path / "site"
    dst.mkdir()
    (dst / "site.toml").write_text(
        '[site]\nname = "T"\nrepository = "https://github.com/x/theme"\nbranch = "main"\n',
        encoding="utf-8",
    )
    patch_site_toml(dst, port=9999, source=repo)
    patched = (dst / "site.toml").read_text(encoding="utf-8")
    assert 'repository = "https://github.com/pwndbg/pwndbg"' in patched
    assert 'branch = "dev"' in patched


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_repo_default_branch_uses_origin_head(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "symbolic-ref", "HEAD", "refs/heads/other")
    _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    assert repo_default_branch(repo) == "main"
