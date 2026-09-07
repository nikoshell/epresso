"""Error model + safety-guard tests."""

from epresso.errors import ConfigError, ContentError, EpressoError, RouteError
from epresso.site import Site


def test_config_error_on_invalid_toml(tmp_path):
    (tmp_path / "site.toml").write_text("not = [valid\n")
    try:
        Site.load(tmp_path)
        raise AssertionError("expected ConfigError")
    except ConfigError as e:
        assert "invalid site.toml" in str(e)


def test_content_error_on_bad_frontmatter(tmp_path):
    (tmp_path / "content").mkdir()
    (tmp_path / "content.config.py").write_text(
        "from epresso.content import define_collection\n"
        "posts = define_collection('posts', glob='*.md', base='./content')\n"
    )
    (tmp_path / "content" / "bad.md").write_text("---\n: bad yaml ::\n---\nbody\n")
    try:
        Site.load(tmp_path)
        raise AssertionError("expected ContentError")
    except ContentError:
        pass


def test_route_error_on_sidecar_missing_gsp(tmp_path):
    (tmp_path / "pages").mkdir()
    (tmp_path / "pages" / "x.html").write_text("hi")
    (tmp_path / "pages" / "x.py").write_text("SIDE = 1\n")  # no get_static_paths
    site = Site.load(tmp_path)
    try:
        site.resolve_routes()
        raise AssertionError("expected RouteError")
    except RouteError:
        pass


def test_recursion_guard_prevents_hang(tmp_path):
    (tmp_path / "pages").mkdir()
    (tmp_path / "pages" / "x.json.py").write_text(
        "def get():\n    site.resolve_routes()\n    return 'application/json', '{}'\n"
    )
    site = Site.load(tmp_path)
    try:
        site.resolve_routes()
        raise AssertionError("expected RouteError (recursion guard)")
    except RouteError as e:
        assert "recursive" in str(e)


def test_error_message_has_location_and_fix():
    e = EpressoError("boom", path="pages/x.md", line=3, fix="add a title")
    s = str(e)
    assert "pages/x.md:3" in s
    assert "add a title" in s


def test_error_categories():
    assert ConfigError("x").category == "config error"
    assert ContentError("x").category == "content error"
    assert RouteError("x").category == "route error"
