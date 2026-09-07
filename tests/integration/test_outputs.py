"""Generated outputs — sitemap, robots, 404, search-index, RSS helper."""

from epresso.site import Site


def _make(files, site_toml=None):
    import tempfile
    from pathlib import Path

    d = tempfile.mkdtemp()
    root = Path(d)
    if site_toml:
        (root / "site.toml").write_text(site_toml, encoding="utf-8")
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root, Site.load(root)


def test_sitemap_generated(site):
    site.build()
    xml = (site.config.dir_output() / "sitemap.xml").read_text()
    assert "<urlset" in xml
    assert "<loc>https://example.com/</loc>" in xml
    assert "/blog/a/" in xml


def test_sitemap_escapes_urls(site):
    import xml.etree.ElementTree as ET

    from epresso import outputs
    from epresso.routing import Route

    site.build()
    out = site.config.dir_output()
    (out / "sitemap.xml").unlink()  # write_sitemap skips when the file already exists
    routes = [Route(path="/docs/a&b/")]
    outputs.write_sitemap(site, out, routes)
    xml = (out / "sitemap.xml").read_text()
    assert "&amp;" in xml
    assert "&lt;" not in xml
    ET.fromstring(xml)  # must be well-formed


def test_robots_generated(site):
    site.build()
    robots = (site.config.dir_output() / "robots.txt").read_text()
    assert "User-agent: *" in robots
    assert "sitemap.xml" in robots


def test_rss_generated_from_collection(site):
    from epresso.config import RssConfig

    site.config.seo.rss = RssConfig(
        enabled=True, collection="posts", path="/feed.xml", url_template="/posts/{id}/"
    )
    site.build()
    xml = (site.config.dir_output() / "feed.xml").read_text()
    assert '<rss version="2.0">' in xml
    assert "<title>A</title>" in xml
    assert "https://example.com/posts/a/" in xml
    assert "<title>B</title>" in xml
    assert "https://example.com/posts/b/" in xml
    assert "01 Jan 2026" in xml  # b's date, formatted as RFC-822 pubDate


def test_rss_disabled_skipped(site):
    site.build()
    assert not (site.config.dir_output() / "rss.xml").exists()


def test_404_generated_default(site):
    site.build()
    html = (site.config.dir_output() / "404.html").read_text()
    assert "404" in html


def test_404_promoted_from_pages_404(tmp_path):
    root, site = _make(
        {
            "pages/404.md": "---\ntitle: Not Found\n---\n# 404 Custom\n",
        }
    )
    site.build()
    html = (site.config.dir_output() / "404.html").read_text()
    assert "404 Custom" in html


def test_search_index_when_enabled(tmp_path):
    root, site = _make(
        {"pages/index.md": "---\ntitle: Home\n---\n# Welcome home\n"},
        site_toml="[search]\nenabled = true\n",
    )
    site.build()
    import json

    data = json.loads((site.config.dir_output() / "search-index.json").read_text())
    assert data["version"] == 2
    assert "index" in data and "units" in data and "avgdl" not in data
    assert data["units"][0]["url"] == "/"


def test_seo_disabled(site):
    site.config.seo.sitemap = False
    site.config.seo.robots = False
    site.build()
    out = site.config.dir_output()
    assert not (out / "sitemap.xml").exists()
    assert not (out / "robots.txt").exists()


def test_rss_helper(site):
    xml = site.rss(
        title="Blog",
        description="Feed",
        path="/feed.xml",
        items=[{"title": "A", "url": "/a/", "date": "2026-01-01", "summary": "s"}],
    )
    assert "<rss version=\"2.0\">" in xml
    assert "<title>A</title>" in xml
    assert "https://example.com/a/" in xml


def test_rss_helper_escapes_xml(site):
    import xml.etree.ElementTree as ET

    xml = site.rss(
        title="News & Updates",
        description="a < b & c",
        path="/feed.xml",
        items=[{"title": "Incremental builds & caching", "url": "/x/?a=1&b=2", "summary": "<b>bold</b> & more"}],
    )
    assert "Incremental builds &amp; caching" in xml
    assert "&lt;b&gt;bold&lt;/b&gt; &amp; more" in xml
    assert "a=1&amp;b=2" in xml  # URL query param escaped
    ET.fromstring(xml)  # must be well-formed


def test_seo_template_helper(site):
    site._do_load()
    tag = site.env.from_string("{{ seo(title='T', description='D', path='/x/') }}").render({})
    assert "<title>T</title>" in tag
    assert "og:title" in tag
    assert "canonical" in tag


def test_default_layout_for_direct_markdown(tmp_path):
    root, site = _make(
        {
            "layouts/Base.ep": (
                "<!doctype html><html><head><title>{% block title %}{{ page.title }}{% endblock %}</title></head>"
                "<body>{% block content %}{{ content | safe }}{% endblock %}</body></html>\n"
            ),
            "pages/page.md": "---\ntitle: Hello\n---\n# Welcome\n",
        },
        site_toml="[markdown]\ndefault_layout = \"Base.ep\"\n",
    )
    site.build()
    html = (root / "dist" / "page" / "index.html").read_text()
    assert "<title>Hello</title>" in html
    assert "Welcome" in html


def test_empty_body_entry_renders_without_crash(tmp_path):
    # A collection entry with no body (e.g. heading-only, h1 stripped) must still
    # get a rendered (empty) content, not leave content Undefined.
    root, site = _make(
        {
            "content.config.py": (
                "from epresso.content import define_collection\n"
                "docs = define_collection('docs', loader=lambda: [{'id':'x','data':{'title':'X'},'body':''}])\n"
            ),
            "pages/docs/[slug].ep": (
                "---\nfrom epresso.routing import Route\n"
                "def get_static_paths():\n"
                "    return [Route(path='/docs/x/', params={'slug':'x'}, data=site.get_entry('docs','x'))]\n"
                "---\n<Base>{{ content | safe }}</Base>\n"
            ),
            "layouts/Base.ep": (
                "---\n---\n<!doctype html><html><head><title>T</title></head>"
                "<body><slot/></body></html>\n"
            ),
        }
    )
    site.build()
    html = (root / "dist" / "docs" / "x" / "index.html").read_text()
    assert "<body></body>" in html

def test_build_populates_perf(site):
    result = site.build()
    assert result.perf  # phase timings recorded
    assert "render" in result.perf and "outputs" in result.perf
    assert result.perf["render"] >= 0 and result.duration > 0
