"""Theme scaffolding tests (`epresso new docs/blog`)."""

import shutil
import subprocess
from pathlib import Path

import pytest

from epresso import themes


# Bundled theme starters live in src/epresso/themes/, which is temporarily
# removed (will be recreated later). Skip the bundled-fallback tests until
# the starters exist again.
def _no_bundled(name: str) -> bool:
    return themes.bundled_starter(name) is None


def _write_repo(root: Path) -> None:
    """Write a minimal theme repo (including git history) into ``root``."""
    (root / "site.toml").parent.mkdir(parents=True, exist_ok=True)
    (root / "site.toml").write_text("name = 'test'\n")
    (root / "content.config.py").write_text("# theme config\n")
    (root / "layouts" / "Base.ep").parent.mkdir(parents=True, exist_ok=True)
    (root / "layouts" / "Base.ep").write_text("---\n---\n<html></html>\n")
    (root / ".git" / "HEAD").parent.mkdir(parents=True, exist_ok=True)
    (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n")


def test_list_themes():
    names = themes.list_themes()
    assert "docs" in names and "blog" in names


def test_scaffold_docs_from_local_repo(tmp_path, monkeypatch):
    repo = tmp_path / "theme-repo"
    _write_repo(repo)
    monkeypatch.setitem(themes.REGISTRY, "docs", (str(repo), "main"))
    dest = tmp_path / "site"
    msg = themes.scaffold("docs", dest)
    assert "copied from" in msg  # prefers the local theme repo
    assert (dest / "site.toml").exists()
    assert (dest / "content.config.py").exists()
    assert (dest / "layouts" / "Base.ep").exists()
    assert not (dest / ".git").exists()  # git history stripped


@pytest.mark.skipif(_no_bundled("blog"), reason="bundled theme starters not present yet")
def test_scaffold_blog_files(tmp_path):
    dest = tmp_path / "site"
    themes.scaffold("blog", dest)
    assert (dest / "pages" / "posts" / "[slug].ep").exists()
    assert (dest / "content" / "posts" / "hello.md").exists()
    assert (dest / "pages" / "feed.xml.py").exists()


@pytest.mark.skipif(_no_bundled("docs"), reason="bundled theme starters not present yet")
def test_scaffold_falls_back_to_bundled_when_no_local(tmp_path, monkeypatch):
    # point the registry at a nonexistent repo so it must use the bundled starter
    monkeypatch.setitem(themes.REGISTRY, "docs", (str(tmp_path / "missing"), "main"))
    monkeypatch.setattr(themes.shutil, "which", lambda _: None)  # no git either
    dest = tmp_path / "site"
    msg = themes.scaffold("docs", dest)
    assert "bundled" in msg
    assert (dest / "site.toml").exists()


def test_scaffold_unknown_theme_raises(tmp_path):
    try:
        themes.scaffold("nope", tmp_path)
        raise AssertionError("expected KeyError")
    except KeyError:
        pass


def test_scaffold_docs_uses_in_repo_theme(tmp_path):
    """`epresso new docs` copies the theme that ships in this repo (themes/docs)."""
    repo = Path(themes.REGISTRY["docs"][0])
    if not repo.is_dir():
        pytest.skip("in-repo themes/docs not present (installed package)")
    dest = tmp_path / "site"
    msg = themes.scaffold("docs", dest)
    assert "copied from" in msg
    assert (dest / "site.toml").exists()
    assert (dest / "layouts" / "Base.ep").exists()
    assert (dest / "pages").is_dir()
    # build artifacts are never scaffolded
    assert not (dest / "dist").exists()
    assert not (dest / ".cache").exists()


@pytest.mark.skipif(_no_bundled("docs"), reason="bundled theme starters not present yet")
def test_scaffolded_theme_builds(tmp_path):
    dest = tmp_path / "site"
    themes.scaffold("docs", dest)

    from epresso.site import Site

    site = Site.load(dest)
    result = site.build()
    out = site.config.dir_output()
    assert (out / "index.html").exists()
    assert any(p.startswith("/docs/") for p in result.pages)


# -- direct sources: directory path or git URL ------------------------------


def test_scaffold_from_directory_path(tmp_path):
    repo = tmp_path / "theme-src"
    _write_repo(repo)
    dest = tmp_path / "site"
    msg = themes.scaffold(str(repo), dest)
    assert "copied from" in msg
    assert (dest / "site.toml").exists()
    assert (dest / "content.config.py").exists()
    assert not (dest / ".git").exists()


def test_parse_source_directory(tmp_path):
    d = tmp_path / "theme"
    d.mkdir()
    assert themes.parse_source(str(d)) == (str(d), None)


@pytest.mark.parametrize(
    ("source", "repo", "ref"),
    [
        ("github:owner/repo", "https://github.com/owner/repo", None),
        ("github:owner/repo@v1", "https://github.com/owner/repo", "v1"),
        ("https://github.com/owner/repo.git", "https://github.com/owner/repo.git", None),
        ("https://github.com/owner/repo.git@v2", "https://github.com/owner/repo.git", "v2"),
        ("git+ssh://git@github.com/owner/repo.git", "ssh://git@github.com/owner/repo.git", None),
        ("git@github.com:owner/repo.git", "git@github.com:owner/repo.git", None),
        ("git@github.com:owner/repo.git@v3", "git@github.com:owner/repo.git", "v3"),
    ],
)
def test_parse_source_git(source, repo, ref):
    assert themes.parse_source(source) == (repo, ref)


def test_parse_source_none_for_unknown_name():
    assert themes.parse_source("nope") is None


def test_scaffold_missing_directory_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="does not exist"):
        themes.scaffold(str(tmp_path / "missing-theme"), tmp_path / "site")


def test_scaffold_clones_git_source(tmp_path, monkeypatch):
    calls: dict = {}

    def fake_run(cmd, **kw):
        calls["cmd"] = cmd
        return object()

    monkeypatch.setattr(themes.shutil, "which", lambda _: "/usr/bin/git")
    monkeypatch.setattr(themes.subprocess, "run", fake_run)
    msg = themes.scaffold("github:owner/repo@v1", tmp_path / "site")
    assert "cloned" in msg
    assert calls["cmd"][:3] == ["/usr/bin/git", "clone", "--depth=1"]
    assert ["--branch", "v1"] == calls["cmd"][3:5]
    assert calls["cmd"][-2] == "https://github.com/owner/repo"


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_scaffold_clones_real_repo(tmp_path):
    """A file:// URL exercises the real git clone path (no network)."""
    repo = tmp_path / "upstream"
    (repo / "pages").mkdir(parents=True)
    (repo / "site.toml").write_text("name = 'test'\n", encoding="utf-8")
    (repo / "pages" / "index.ep").write_text("---\n---\n<p>hi</p>\n", encoding="utf-8")
    git = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run([*git, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-qm", "init"], cwd=repo, check=True)

    dest = tmp_path / "site"
    msg = themes.scaffold(f"file://{repo}", dest)
    assert "cloned" in msg
    assert (dest / "site.toml").exists()
    assert (dest / "pages" / "index.ep").exists()
    assert not (dest / ".git").exists()
