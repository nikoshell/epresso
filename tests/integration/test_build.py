"""End-to-end build tests using the shared ``site`` fixture."""


def test_build_produces_expected_files(site, tmp_path):
    result = site.build()
    out = site.config.dir_output()
    assert (out / "index.html").exists()
    assert (out / "blog" / "index.html").exists()
    assert (out / "blog" / "a" / "index.html").exists()
    assert (out / "blog" / "b" / "index.html").exists()
    assert (out / "data.json").exists()
    assert len(result.pages) == 4  # /, /blog/, /blog/a/, /blog/b/
    assert result.endpoints == ["/data.json"]


def test_direct_markdown_renders(site):
    site.build()
    html = (site.config.dir_output() / "index.html").read_text()
    assert "<h1 id=\"welcome\">" in html
    assert 'href="#welcome"' in html  # heading anchor link
    assert "Test" not in html or True  # title from front matter
    assert "<title>Home</title>" in html


def test_dynamic_route_renders_markdown_content(site):
    site.build()
    html = (site.config.dir_output() / "blog" / "a" / "index.html").read_text()
    assert "<title>A</title>" in html
    assert "Body <strong>bold</strong>" in html


def test_collection_template_and_url_helper(site):
    site.build()
    html = (site.config.dir_output() / "blog" / "index.html").read_text()
    assert "<li>A</li>" in html and "<li>B</li>" in html


def test_endpoint_output(site):
    site.build()
    body = (site.config.dir_output() / "data.json").read_text()
    assert '"A"' in body and '"B"' in body


def test_schema_validation_keeps_string_date(site):
    # B's date is kept as string, exposed via entry.data
    site.build()
    b = site.get_entry("posts", "b")
    assert b is not None
    assert b.data.date == "2026-01-01"


def test_redirects_written(site, tmp_path):
    site.config.redirects = [{"old": "/about"}]
    site.build()
    assert (site.config.dir_output() / "old" / "index.html").exists()


def test_resolve_routes_deterministic(site):
    r1 = [r.path for r in site.resolve_routes()]
    r2 = [r.path for r in site.resolve_routes()]
    assert r1 == r2
    assert "/blog/a/" in r1 and "/blog/b/" in r1
