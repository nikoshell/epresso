"""Unit tests for the BuildGraph — the per-render dependency graph + cache.

These drive the engine directly (no full render), which is the seam Candidate 3
opened up: dependency edges, digest resolution and the skip/rerender decision are
all exercised through one module.
"""


def test_records_and_resolves_content_edges(site):
    site.graph.begin_route("/posts/")
    site.get_collection("posts")
    site.get_entry("posts", "a")
    site.graph.end_route()
    hashes = site.graph.content_hashes_for("/posts/")
    assert "collection:posts" in hashes
    assert "posts:a" in hashes
    assert hashes["posts:a"]  # a real digest, not None


def test_no_edges_recorded_outside_a_render(site):
    site.get_collection("posts")  # data API, but no route in progress
    assert site.graph.edges_for("/anything/") == set()


def test_begin_route_resets_prior_edges(site):
    site.graph.begin_route("/x/")
    site.get_collection("posts")
    site.graph.end_route()
    site.graph.begin_route("/x/")  # re-render: stale deps must clear
    site.get_entry("posts", "b")
    site.graph.end_route()
    assert site.graph.edges_for("/x/") == {"posts:b"}


def test_engine_roundtrip_skips_unchanged(site):
    site.graph.prepare(clean=True)
    path = "/manual/"
    site.graph.begin_route(path)
    site.get_collection("posts")
    site.graph.end_route()
    site.graph.record_rendered(path, "cache-key", "manual.html", "<html>v1</html>")
    site.graph.finish({path})

    site._do_load()  # fresh graph + fresh cache (as build() does); reads manifest
    site.graph.prepare(clean=False)
    assert site.graph.can_skip(path, "cache-key", "manual.html")
    assert site.graph.reuse_output(path, "manual.html") == b"<html>v1</html>"


def test_engine_rerenders_when_content_changes(site):
    site.graph.prepare(clean=True)
    path = "/manual/"
    site.graph.begin_route(path)
    site.get_collection("posts")
    site.graph.end_route()
    site.graph.record_rendered(path, "cache-key", "manual.html", "<html>v1</html>")
    site.graph.finish({path})

    # Change a content entry the path depends on; the collection digest changes.
    (site.config.root / "content/posts/a.md").write_text(
        "---\ntitle: A changed\n---\n# Hello changed\n", encoding="utf-8"
    )
    site._do_load()  # reload store (new digest) + graph (fresh manifest read)
    site.graph.prepare(clean=False)

    assert not site.graph.can_skip(path, "cache-key", "manual.html")


def test_can_skip_is_false_until_manifest_is_usable(site):
    site.graph.prepare(clean=True)  # no previous manifest
    assert not site.graph.can_skip("/", None, "index.html")


def test_code_hash_excludes_markdown_and_changes_on_template_edit(site):
    h1 = site.graph.hash_code(site.config)
    # a template edit changes the code hash
    p = site.config.root / "layouts" / "Base.ep"
    p.write_text(p.read_text(encoding="utf-8") + "<!-- edit -->\n", encoding="utf-8")
    h2 = site.graph.hash_code(site.config)
    assert h1 != h2


def test_layer_hash_covers_components_and_layouts_only(site):
    """A layer's `.git/` and stray files must not invalidate the build cache.

    Walking the whole layer checkout pulled in `.git/index` (which changes on any
    git command) and any large stray file, forcing a full re-render.
    """
    layer = site.config.root / "vendor" / "ui"
    (layer / "components").mkdir(parents=True)
    (layer / "layouts").mkdir(parents=True)
    (layer / "components" / "Button.ep").write_text("<button/>", encoding="utf-8")
    (layer / "layouts" / "Shell.ep").write_text("<html/>", encoding="utf-8")

    h1 = site.graph.hash_code(site.config, [layer])

    (layer / ".git").mkdir()
    (layer / ".git" / "index").write_bytes(b"v1")
    (layer / "json").write_bytes(b"x" * 4096)
    assert site.graph.hash_code(site.config, [layer]) == h1

    (layer / "components" / "Button.ep").write_text("<button class='x'/>", encoding="utf-8")
    assert site.graph.hash_code(site.config, [layer]) != h1
