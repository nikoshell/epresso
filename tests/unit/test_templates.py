"""Template engine tests — curated globals, layouts, error handling."""

from markupsafe import Markup

from epresso.errors import TemplateError
from epresso.templates import render_markdown_page, render_template


def test_url_helper(site):
    site._do_load()
    html = render_template(site.env, "layouts/base.html", {"page": {}})
    assert "<html>" in html


def test_curated_globals_in_template(site):
    site._do_load()
    out = render_template(
        site.env,
        "layouts/base.html",
        {"page": {"title": "T"}, "content": Markup("x")},
    )
    assert "<title>T</title>" in out


def test_url_and_asset_via_template(site, tmp_path):
    site.config.build.trailing_slash = "always"
    site._do_load()
    # render an inline template using the url() and asset() globals
    tpl = site.env.from_string("{{ url('/blog/hello') }}|{{ url('/data.json') }}|{{ asset('css/main.css') }}")
    out = tpl.render({})
    # asset() resolves under /assets/; the file doesn't exist here, so it stays un-hashed
    assert out == "/blog/hello/|/data.json|/assets/css/main.css"


def test_get_collection_get_entry_via_template(site):
    site._do_load()
    tpl = site.env.from_string(
        "{% for p in get_collection('posts') %}{{ p.data.title }};{% endfor %}"
        "{{ get_entry('posts', 'a').data.title }}"
    )
    out = tpl.render({})
    assert out.startswith("A;B;")
    assert "A" in out


def test_markdown_page_block_layout(site, tmp_path):
    site._do_load()
    layout = "layouts/base.html"
    html = render_markdown_page(
        site.env,
        title="P",
        content_html="<p>hi</p>",
        frontmatter={"title": "P"},
        layout=layout,
        site=site,
        route_path="/p/",
    )
    assert "<title>P</title>" in html
    assert "<p>hi</p>" in html


def test_markdown_page_no_layout(site):
    site._do_load()
    html = render_markdown_page(
        site.env,
        title="P",
        content_html="<h1>hi</h1>",
        frontmatter={"title": "P"},
        layout=None,
        site=site,
        route_path="/p/",
    )
    assert "<title>P</title>" in html and "<h1>hi</h1>" in html


def test_unknown_template_raises(site):
    site._do_load()
    try:
        render_template(site.env, "does/not/exist.html", {})
        raise AssertionError("expected TemplateError")
    except TemplateError:
        pass
