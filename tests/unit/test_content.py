from pydantic import BaseModel

from epresso.content import ContentStore, define_collection
from epresso.content.store import content_digest
from epresso.document import parse_document


class Post(BaseModel):
    title: str
    date: str = ""


def test_front_matter_split():
    raw = "---\ntitle: Hi\ndate: 2026-01-01\n---\n\n# Body\n"
    doc = parse_document(raw, "markdown")
    assert doc.data["title"] == "Hi"
    # date must stay a string (no timestamp coercion)
    assert doc.data["date"] == "2026-01-01"
    assert doc.body.strip() == "# Body"


def test_front_matter_absent():
    doc = parse_document("# no front matter", "markdown")
    assert doc.data == {}
    assert doc.body == "# no front matter"


def test_digest_is_stable_and_sensitive():
    a = content_digest("body", {"title": "x"})
    b = content_digest("body", {"title": "x"})
    c = content_digest("body", {"title": "y"})
    d = content_digest("body2", {"title": "x"})
    assert a == b
    assert a != c
    assert a != d


def test_python_loader_remote_data(tmp_path):
    """A custom (e.g. remote) loader feeds a collection (M4 — build-time remote data)."""
    from epresso.content import ContentStore, define_collection

    def fetch():
        # simulates fetching JSON at build time
        return [{"id": "a", "data": {"title": "Alpha"}}, {"id": "b", "data": {"title": "Beta"}}]

    dc = define_collection("posts", loader=fetch, schema=Post)
    store = ContentStore()
    col = dc.install(store)
    col.loader.load(store, col)
    assert col.get("a").data.title == "Alpha"
    assert len(col.all()) == 2


def test_data_collection_json(tmp_path):
    """A JSON data file becomes a collection entry (C1 — YAML/JSON/TOML data)."""
    import json

    from epresso.content import ContentStore, define_collection

    (tmp_path / "content" / "team").mkdir(parents=True)
    (tmp_path / "content" / "team" / "alice.json").write_text(json.dumps({"title": "Alice"}))
    dc = define_collection("team", glob="*.json", base="./content/team", schema=Post)
    store = ContentStore()
    col = dc.install(store)
    col.loader.base = (tmp_path / col.loader.base).resolve()
    col.loader.load(store, col)
    entry = col.get("alice")
    assert entry is not None and entry.data.title == "Alice"


def test_glob_loader_keeps_date_strings(tmp_path):
    (tmp_path / "content" / "posts").mkdir(parents=True)
    (tmp_path / "content" / "posts" / "p.md").write_text(
        "---\ntitle: P\ndate: 2026-01-01\n---\nbody\n"
    )
    dc = define_collection("posts", glob="*.md", base="./content/posts", schema=Post)
    store = ContentStore()
    col = dc.install(store)
    col.loader.base = (tmp_path / col.loader.base).resolve()
    col.loader.load(store, col)
    entry = col.get("p")
    assert entry is not None
    assert entry.data.title == "P"
    assert entry.data.date == "2026-01-01"


def test_glob_loader_skips_underscore_prefix(tmp_path):
    (tmp_path / "content" / "posts").mkdir(parents=True)
    (tmp_path / "content" / "posts" / "a.md").write_text("---\ntitle: A\n---\nbody")
    (tmp_path / "content" / "posts" / "_draft.md").write_text("---\ntitle: Draft\n---\nbody")
    (tmp_path / "content" / "posts" / "_partials").mkdir()
    (tmp_path / "content" / "posts" / "_partials" / "x.md").write_text("---\ntitle: X\n---\nbody")

    dc = define_collection("posts", glob="**/*.md", base="./content/posts", schema=Post)
    store = ContentStore()
    col = dc.install(store)
    col.loader.base = (tmp_path / col.loader.base).resolve()
    col.loader.load(store, col)

    assert sorted(col.entries) == ["a"]
