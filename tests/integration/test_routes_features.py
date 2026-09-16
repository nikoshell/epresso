"""Route-feature integration tests: spread routes, endpoint content types, redirects."""

from epresso.site import Site


def make(files):
    import tempfile
    from pathlib import Path

    d = tempfile.mkdtemp()
    root = Path(d)
    base = {
        "site.toml": "[build]\ntrailing_slash = 'always'\n",
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
            "pages/docs/[...path].ep": (
                "---\n"
                "from epresso.routing import Route\n"
                "def get_static_paths():\n"
                "    return [Route(path='/docs/a/b/', params={'path': ['a','b']})]\n"
                "---\n"
                "<p>path={{ params['path']|join('/') }}</p>\n"
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
    root, site = make({"pages/index.md": "---\ntitle: Home\n---\nHi\n"})
    site.config.redirects = [{"/old": "/new"}]
    site.build()
    rd = site.config.dir_output() / "old" / "index.html"
    assert rd.exists()
    assert "url=/new" in rd.read_text()


def test_clean_urls_and_trailing_slash(tmp_path):
    root, site = make({"pages/about.md": "---\ntitle: About\n---\nAbout us\n"})
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


def test_ep_page_template_can_emit_its_own_body_routes(tmp_path):
    """A `.ep` page template may return non-HTML routes from get_static_paths().

    Their body is written verbatim (no page template, no scoped CSS/JS) — the
    mechanism the docs theme uses to serve each page's markdown at `<page>.md`.
    """
    root, site = make(
        {
            "pages/doc.ep": (
                "---\n"
                "from epresso.routing import Route\n"
                "def get_static_paths():\n"
                "    return [\n"
                "        Route(path='/doc/', params={}),\n"
                "        Route(\n"
                "            path='/doc.md',\n"
                "            content_type='text/markdown; charset=utf-8',\n"
                "            body='# Doc\\n\\nbody text\\n',\n"
                "        ),\n"
                "    ]\n"
                "---\n"
                "<html><body><h1>Doc</h1></body></html>\n"
            ),
        }
    )
    result = site.build()
    out = root / "dist"
    assert (out / "doc/index.html").exists()
    md = (out / "doc.md").read_text(encoding="utf-8")
    assert md == "# Doc\n\nbody text\n"
    # not wrapped by the page template, and routed as an endpoint not a page
    assert "<h1>Doc</h1>" not in md
    assert "/doc/" in result.pages
    assert "/doc.md" in result.endpoints
