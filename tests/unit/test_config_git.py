"""Config defaults: when a project lives in a git repo, site.repository and
site.branch default to the repo's origin URL and HEAD branch."""

import shutil
import subprocess
from pathlib import Path

import pytest

from epresso.config import load_config


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def _init_repo(root: Path, *, url: str = "https://github.com/acme/project.git", branch: str = "main") -> None:
    _git(root, "init", "-q")
    _git(root, "symbolic-ref", "HEAD", f"refs/heads/{branch}")
    _git(root, "remote", "add", "origin", url)


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_defaults_from_git_repo(tmp_path: Path):
    _init_repo(tmp_path)
    (tmp_path / "site.toml").write_text('[site]\nname = "S"\nurl = "https://x.example"\n', encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg.site.repository == "https://github.com/acme/project"  # .git stripped
    assert cfg.site.branch == "main"


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_git_uses_checked_out_branch(tmp_path: Path):
    _init_repo(tmp_path, branch="develop")
    (tmp_path / "site.toml").write_text('[site]\nname = "S"\n', encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg.site.branch == "develop"


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_default_branch_prefers_origin_head(tmp_path: Path):
    # checked out on dev, but the repo's recorded default is main -> use main
    _init_repo(tmp_path, branch="dev")
    _git(tmp_path, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    (tmp_path / "site.toml").write_text('[site]\nname = "S"\n', encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg.site.branch == "main"


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_explicit_repository_and_branch_win(tmp_path: Path):
    _init_repo(tmp_path, branch="main")
    (tmp_path / "site.toml").write_text(
        '[site]\nrepository = "https://custom.example/r"\nbranch = "release"\n', encoding="utf-8"
    )
    cfg = load_config(tmp_path)
    assert cfg.site.repository == "https://custom.example/r"
    assert cfg.site.branch == "release"


def test_no_git_keeps_defaults(tmp_path: Path):
    (tmp_path / "site.toml").write_text('[site]\nname = "S"\n', encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg.site.repository == ""
    assert cfg.site.branch == "main"
