"""Unit tests for the docs-scaffolding helpers (epresso.docsgen)."""

import shutil
import subprocess
from pathlib import Path

import pytest

from epresso.docsgen import (
    auto_docs_project,
    is_repo_dir,
    materialize_docs_source,
    normalize_repo_url,
    patch_site_toml,
    repo_default_branch,
    repo_origin,
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


def _commit(root: Path, msg: str = "init") -> None:
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", msg)


def _make_repo(root: Path, files: dict[str, str], branch: str = "main") -> Path:
    root.mkdir(parents=True)
    for rel, content in files.items():
        _write(root, rel, content)
    _git(root, "init", "-q", "-b", branch)
    _commit(root)
    return root


def test_materialize_docs_source_returns_existing_directory(tmp_path):
    src = tmp_path / "docs-src"
    src.mkdir()
    assert materialize_docs_source(str(src), tmp_path / "cache") == src.resolve()


def test_materialize_docs_source_unknown_spec_is_none(tmp_path):
    assert materialize_docs_source("not-a-repo-and-not-a-path", tmp_path / "cache") is None


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_materialize_docs_source_clones_a_git_url_and_caches_it(tmp_path):
    repo = _make_repo(tmp_path / "repo", {"docs/index.md": "# Hi\n", "README.md": "# Repo\n"})
    cache = tmp_path / "cache"
    clone = materialize_docs_source(f"file://{repo}", cache)
    assert clone is not None and clone.is_dir()
    # .git is kept so patch_site_toml can read origin/branch for the repo link
    assert (clone / ".git").exists()
    assert repo_origin(clone).startswith("file://")
    assert (clone / "docs" / "index.md").is_file()
    # a second call reuses the cached clone rather than re-fetching
    sentinel = clone / "SENTINEL"
    sentinel.write_text("x", encoding="utf-8")
    assert materialize_docs_source(f"file://{repo}", cache) == clone
    assert sentinel.exists()


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_materialize_docs_source_pins_a_ref(tmp_path):
    repo = _make_repo(tmp_path / "repo", {"docs/index.md": "# main\n"})
    _git(repo, "checkout", "-q", "-b", "v1")
    _write(repo, "docs/extra.md", "# v1 only\n")
    _commit(repo, "v1")
    clone = materialize_docs_source(f"file://{repo}@v1", tmp_path / "cache")
    assert clone is not None
    assert (clone / "docs" / "extra.md").is_file()


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_materialize_docs_source_rejects_a_bad_ref(tmp_path):
    from epresso.errors import EpressoError

    repo = _make_repo(tmp_path / "repo", {"docs/index.md": "# Hi\n"})
    with pytest.raises(EpressoError, match="could not fetch docs"):
        materialize_docs_source(f"file://{repo}@no-such-ref", tmp_path / "cache")


def test_branding_styles_css_lands_in_the_theme_stylesheet(tmp_path):
    from epresso.docsgen import auto_docs_project

    src = tmp_path / "md"
    src.mkdir()
    (src / "index.md").write_text("# Hi\n\nx\n", encoding="utf-8")
    (src / "styles.css").write_text(":root { --brand-marker: 1; }\n", encoding="utf-8")
    proj = auto_docs_project(src, 4321)
    assert "--brand-marker" in (proj / "styles" / "docs.css").read_text(encoding="utf-8")


def test_auto_docs_project_names_the_site_after_the_source(tmp_path):
    import tomllib

    from epresso.docsgen import auto_docs_project

    src = tmp_path / "pwndbg"
    src.mkdir()
    (src / "index.md").write_text("# Hi\n\nx\n", encoding="utf-8")
    proj = auto_docs_project(src, 4321)
    assert tomllib.loads((proj / "site.toml").read_text(encoding="utf-8"))["site"]["name"] == "pwndbg"


def test_epresso_brand_dot_is_dropped_for_other_projects_and_kept_via_docs_toml(tmp_path):
    import tomllib

    from epresso.docsgen import auto_docs_project, docs_toml_project
    from epresso.themes import bundled_docs_theme

    assert tomllib.loads((bundled_docs_theme() / "site.toml").read_text())["theme"]["brand_dot"] is True
    src = tmp_path / "proj"
    (src / "docs").mkdir(parents=True)
    (src / "docs" / "index.md").write_text("# Hi\n\nx\n", encoding="utf-8")
    other = tomllib.loads((auto_docs_project(src, 4321) / "site.toml").read_text())
    assert "brand_dot" not in other["theme"]
    (src / "docs.toml").write_text('[theme]\nbrand_dot = true\n', encoding="utf-8")
    ours = tomllib.loads((docs_toml_project(src / "docs.toml", 4321) / "site.toml").read_text())
    assert ours["theme"]["brand_dot"] is True


def test_epresso_redirects_do_not_leak_into_other_projects(tmp_path):
    import tomllib

    from epresso.docsgen import auto_docs_project

    src = tmp_path / "proj"
    src.mkdir()
    (src / "index.md").write_text("# Hi\n\nx\n", encoding="utf-8")
    cfg = tomllib.loads((auto_docs_project(src, 4321) / "site.toml").read_text())
    assert "redirects" not in cfg
