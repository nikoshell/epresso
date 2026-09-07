"""`epresso inspect` (build graph) and `epresso deploy` tests."""


from epresso.deploy import gh_pages
from epresso.site import Site


def _make(files):
    import tempfile
    from pathlib import Path

    d = tempfile.mkdtemp()
    root = Path(d)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root, Site.load(root)


def test_build_graph_routes_and_edges(site):
    site._do_load()
    g = site.build_graph()
    assert "/" in g["routes"]
    assert "/blog/" in g["routes"]
    # the blog index lists the posts collection → an edge
    assert g["edges"]["/blog/"] == ["collection:posts"]


def test_graph_dot(site):
    site._do_load()
    dot = site.graph_dot()
    assert dot.startswith("digraph epresso {")
    assert 'collection:posts" -> "/blog/"' in dot


def test_gh_pages_no_push_builds_and_commits(site):
    msg = gh_pages(site, remote="origin", branch="gh-pages", push=False)
    assert "built (not pushed)" in msg
    assert "gh-pages" in msg


def test_gh_pages_requires_git(site, monkeypatch):
    monkeypatch.setattr("epresso.deploy.shutil.which", lambda _: None)
    try:
        gh_pages(site, push=False)
        raise AssertionError("expected RuntimeError")
    except RuntimeError as e:
        assert "git is required" in str(e)
