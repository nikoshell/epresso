"""Content references (reference()) and get_entries/get_tags tests."""

from epresso.content import reference


def test_reference_usable_in_schema():
    from pydantic import BaseModel, TypeAdapter

    ta = TypeAdapter(reference("authors"))
    assert ta.validate_python("a") == "a"

    class Post(BaseModel):
        author: reference("authors")

    p = Post(author="alice")
    assert p.author == "alice"


def test_get_entries_resolves_and_records_edges(site):
    site._do_load()
    site.graph.begin_route("/x/")
    entries = site.get_entries("posts", ["a", "b"])
    assert [e.id for e in entries] == ["a", "b"]
    assert "posts:a" in site.graph.edges_for("/x/")
    site.graph.end_route()


def test_get_entries_raises_on_missing(site):
    site._do_load()
    try:
        site.get_entries("posts", ["nope"])
        raise AssertionError("expected ContentError")
    except Exception as e:
        assert "unknown content reference" in str(e)


def test_get_tags_groups(site):
    site._do_load()
    tags = site.get_tags("posts", field="tags")
    # a has no tags, b has [x, y]
    assert "x" in tags and "y" in tags
    assert [e.id for e in tags["x"]] == ["b"]


def test_reference_in_schema_renders(site):
    # schema using reference() stores a plain string id that get_entries resolves
    site._do_load()
    b = site.get_entry("posts", "b")
    assert b is not None
