"""The repository adapter (epresso.gitrepo): origin URL + default branch."""

import shutil
import subprocess
from pathlib import Path

import pytest

from epresso.gitrepo import default_branch, normalize_repo_url, origin_url


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def _init(root: Path, branch: str = "main", url: str = "git@github.com:a/b.git") -> None:
    _git(root, "init", "-q")
    _git(root, "symbolic-ref", "HEAD", f"refs/heads/{branch}")
    _git(root, "remote", "add", "origin", url)


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_origin_url_normalized(tmp_path: Path):
    _init(tmp_path, url="git@github.com:acme/proj.git")
    assert origin_url(tmp_path) == "https://github.com/acme/proj"


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_default_branch_prefers_origin_head(tmp_path: Path):
    _init(tmp_path, branch="dev")
    _git(tmp_path, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    assert default_branch(tmp_path) == "main"


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_default_branch_falls_back_to_checked_out(tmp_path: Path):
    _init(tmp_path, branch="develop")
    assert default_branch(tmp_path) == "develop"


def test_normalize_repo_url_forms():
    assert normalize_repo_url("git@github.com:a/b.git") == "https://github.com/a/b"
    assert normalize_repo_url("https://github.com/a/b.git") == "https://github.com/a/b"
    assert normalize_repo_url("git://github.com/a/b") == "https://github.com/a/b"
    assert normalize_repo_url(" https://github.com/a/b ") == "https://github.com/a/b"
