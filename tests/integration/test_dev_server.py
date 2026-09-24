"""Dev-server tests using Starlette's TestClient (shared ``site`` fixture)."""

from starlette.testclient import TestClient

from epresso.server import DevServer


def _client(site):
    server = DevServer(site, port=8000)
    return TestClient(server.build_app())


def test_serves_home(site):
    c = _client(site)
    r = c.get("/")
    assert r.status_code == 200
    assert "Welcome" in r.text


def test_serves_dynamic_route(site):
    c = _client(site)
    r = c.get("/blog/a/")
    assert r.status_code == 200
    assert "Body <strong>bold</strong>" in r.text


def test_serves_endpoint_json(site):
    c = _client(site)
    r = c.get("/data.json")
    assert r.status_code == 200
    assert '"A"' in r.text


def test_missing_page_404(site):
    c = _client(site)
    r = c.get("/nope/")
    assert r.status_code == 404


def test_injects_live_reload(site):
    c = _client(site)
    r = c.get("/")
    assert "__epresso_reload" in r.text


def test_dev_injects_page_scripts(site):
    site.config.assets.hash = False  # dev mode
    site._do_load()
    c = _client(site)
    r = c.get("/")
    assert r.status_code == 200


def test_dev_serves_scoped_css_and_scripts_from_last_build(site, tmp_path):
    dist = site.config.dir_output()
    (dist / "_scoped").mkdir(parents=True, exist_ok=True)
    (dist / "_scoped" / "epresso-abc.css").write_text(".x{color:red}", encoding="utf-8")
    (dist / "_epresso" / "scripts").mkdir(parents=True, exist_ok=True)
    (dist / "_epresso" / "scripts" / "abc.js").write_text("console.log(1)", encoding="utf-8")
    c = _client(site)
    assert c.get("/_scoped/epresso-abc.css").status_code == 200
    assert c.get("/_epresso/scripts/abc.js").status_code == 200


def test_static_dist_serves_generated_404(site, tmp_path):
    """serve_dist serves the generated 404.html (with layout) for unknown paths."""
    from starlette.testclient import TestClient

    from epresso.server import _build_static_app

    dist = tmp_path / "dist"
    (dist / "404.html").parent.mkdir(parents=True, exist_ok=True)
    (dist / "404.html").write_text(
        "<!doctype html><html><head><title>404</title></head>"
        "<body><nav>sidebar</nav><h1>404 — Not Found</h1></body></html>"
    )
    (dist / "index.html").write_text("<h1>home</h1>")
    c = TestClient(_build_static_app(dist))
    r = c.get("/nope/")
    assert r.status_code == 404
    assert "sidebar" in r.text
    assert "404 — Not Found" in r.text


def test_dev_serves_sharded_search_index(tmp_path):
    """A multi-section site writes a manifest plus per-section shard files;
    the dev server must serve the shards, not just the manifest."""
    from epresso.site import Site

    (tmp_path / "site.toml").write_text("[search]\nenabled = true\n", encoding="utf-8")
    for rel, body in {
        "pages/index.md": "---\ntitle: Home\n---\n# Welcome home\n",
        "pages/guide/index.md": "---\ntitle: Guide\n---\n# Read the guide\n",
    }.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    c = TestClient(DevServer(Site.load(tmp_path), port=8000).build_app())

    manifest = c.get("/search-index.json").json()
    assert manifest["version"] == 3 and len(manifest["sections"]) == 2
    for sec in manifest["sections"]:
        r = c.get("/" + sec["file"])
        assert r.status_code == 200, sec["file"]
        assert "index" in r.json()
    # Only real shard files are served; traversal out of the shard dir is not.
    assert c.get("/search-index/nope.json").status_code == 404
    assert c.get("/search-index/../site.toml").status_code == 404
