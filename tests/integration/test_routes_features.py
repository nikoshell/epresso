"""Route-feature integration tests: spread routes, endpoint content types, redirects."""

from epresso.site import Site


def make(files):
    import tempfile
    from pathlib import Path

    d = tempfile.mkdtemp()
    root = Path(d)
    base = {
        "site.toml": "[build]\ntrailing_slash = 'always'\n",
        "templates/layouts/base.html": (
            "<html><head><title>{% block title %}epresso{% endblock %}</title></head>"
            "<body>{% block content %}{% endblock %}</body></html>\n"
        ),
    }
    base.update(files)
    for rel, content in base.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root, Site.load(root)


def test_spread_route(tmp_path):
    root, site = make(
        {
            "pages/docs/[...path].html": (
                "{% extends 'layouts/base.html' %}{% block title %}Doc{% endblock %}"
                "{% block content %}path={{ params['path']|join('/') }}{% endblock %}\n"
            ),
            "pages/docs/[...path].py": (
                "from epresso.routing import Route\n"
                "def get_static_paths():\n"
                "    return [Route(path='/docs/a/b/', params={'path': ['a','b']})]\n"
            ),
        }
    )
    site.build()
    out = site.config.dir_output()
    assert (out / "docs" / "a" / "b" / "index.html").exists()
    html = (out / "docs" / "a" / "b" / "index.html").read_text()
    assert "path=a/b" in html


def test_robots_txt_endpoint(tmp_path):
    root, site = make(
        {
            "pages/robots.txt.py": (
                "def get():\n    return 'text/plain', 'User-agent: *\\nAllow: /\\n'\n"
            )
        }
    )
    site.build()
    out = site.config.dir_output()
    assert (out / "robots.txt").exists()
    assert "User-agent" in (out / "robots.txt").read_text()


def test_sitemap_xml_endpoint(tmp_path):
    root, site = make(
        {
            "pages/sitemap.xml.py": (
                "def get():\n"
                "    return 'application/xml', '<urlset><url><loc>/</loc></url></urlset>\\n'\n"
            )
        }
    )
    site.build()
    xml = (site.config.dir_output() / "sitemap.xml").read_text()
    assert "<urlset>" in xml and "<loc>/</loc>" in xml


def test_redirect_meta(tmp_path):
    root, site = make({"pages/index.md": "---\ntitle: Home\nlayout: layouts/base.html\n---\nHi\n"})
    site.config.redirects = [{"/old": "/new"}]
    site.build()
    rd = site.config.dir_output() / "old" / "index.html"
    assert rd.exists()
    assert "url=/new" in rd.read_text()


def test_clean_urls_and_trailing_slash(tmp_path):
    root, site = make({"pages/about.md": "---\ntitle: About\nlayout: layouts/base.html\n---\nAbout us\n"})
    site.build()
    # trailing slash always → directory URL
    assert (site.config.dir_output() / "about" / "index.html").exists()


def test_trailing_slash_never(tmp_path):
    root, site = make(
        {
            "site.toml": "[build]\ntrailing_slash = 'never'\n",
            "pages/about.md": "---\ntitle: About\n---\nAbout\n",
        }
    )
    site.build()
    # with never, still directory output but the built path should be about.html? epresso uses index.html per dir
    # assert the route path has no trailing slash
    paths = [r.path for r in site.resolve_routes()]
    assert "/about" in paths
