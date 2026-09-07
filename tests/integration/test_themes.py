"""Theme scaffolding tests (`epresso new docs/blog`)."""

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
    (root / "templates" / "layouts" / "base.html").parent.mkdir(parents=True, exist_ok=True)
    (root / "templates" / "layouts" / "base.html").write_text("<html></html>\n")
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
    assert (dest / "templates" / "layouts" / "base.html").exists()
    assert not (dest / ".git").exists()  # git history stripped


@pytest.mark.skipif(_no_bundled("blog"), reason="bundled theme starters not present yet")
def test_scaffold_blog_files(tmp_path):
    dest = tmp_path / "site"
    themes.scaffold("blog", dest)
    assert (dest / "pages" / "posts" / "[slug].html").exists()
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
