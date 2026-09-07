from pathlib import Path

from epresso.routing import Route, _build_path, output_path_for, parse_route


def test_parse_static():
    segments, params = parse_route(Path("about.md"))
    assert params == {}
    assert _build_path(segments, {}, "always") == "/about/"


def test_parse_index_is_root():
    segments, params = parse_route(Path("index.md"))
    assert _build_path(segments, {}, "always") == "/"


def test_parse_dynamic():
    segments, params = parse_route(Path("blog/[slug].html"))
    assert params == {"slug": None}
    assert _build_path(segments, {"slug": "hello"}, "always") == "/blog/hello/"


def test_parse_spread():
    segments, params = parse_route(Path("docs/[...path].html"))
    assert params == {"path": None}
    assert _build_path(segments, {"path": ["a", "b"]}, "always") == "/docs/a/b/"


def test_nested_dynamic():
    segments, params = parse_route(Path("sponsor/[sponsor]/[job].html"))
    assert set(params) == {"sponsor", "job"}
    assert _build_path(segments, {"sponsor": "acme", "job": "eng"}, "always") == "/sponsor/acme/eng/"


def test_trailing_slash_never():
    segments, _ = parse_route(Path("about.md"))
    assert _build_path(segments, {}, "never") == "/about"


def test_output_path_directory():
    assert output_path_for("/") == "index.html"
    assert output_path_for("/about/") == "about/index.html"
    assert output_path_for("/blog/hello/") == "blog/hello/index.html"


def test_output_path_file_endpoint():
    assert output_path_for("/robots.txt") == "robots.txt"
    assert output_path_for("/api/data.json") == "api/data.json"


def test_output_path_dir_with_dot_in_name():
    # a directory whose name contains a dot (e.g. a repo named 996.ICU) must
    # still be treated as a directory, not a file endpoint.
    assert output_path_for("/996icu/996.ICU/") == "996icu/996.ICU/index.html"
    assert output_path_for("/996icu/996.ICU/README_CN/") == "996icu/996.ICU/README_CN/index.html"


def test_route_dataclass():
    r = Route(path="/x/", template="x.html", params={"a": 1}, data={"k": "v"})
    assert r.content_type == "text/html"
    assert r.path == "/x/"


def test_is_private():
    from pathlib import Path

    from epresso.private import is_private

    assert is_private(Path("_draft.md"))
    assert is_private(Path("_partials/x.md"))
    assert not is_private(Path("blog/post.md"))
    assert not is_private(Path("about.ep"))


def test_discover_skips_underscore_prefix(tmp_path):
    from epresso.routing import discover_route_patterns

    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "index.ep").write_text("---\n---\nhi")
    (pages / "_draft.ep").write_text("---\n---\ndraft")
    (pages / "_private").mkdir()
    (pages / "_private" / "x.md").write_text("# x")
    (pages / "blog").mkdir()
    (pages / "blog" / "post.md").write_text("# post")

    rels = [p.rel.as_posix() for p in discover_route_patterns(pages)]
    assert "index.ep" in rels
    assert "blog/post.md" in rels
    assert not any(part.startswith("_") for r in rels for part in r.split("/"))
