"""Tests for the `.ep` single-file format (Python frontmatter + Jinja body).

Composition is done with components and ``<slot/>``; legacy Jinja composition
(``{% extends %}/{% block %}/{% include %}/{% component %}``) is rejected, so
these fixtures use layout components + JSX tags only.
"""

from pathlib import Path

import pytest

from epresso.errors import TemplateError
from epresso.site import Site


def _make(files, tmp_path):
    root = Path(tmp_path)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root, Site.load(root)


def _site_files():
    return {
        "site.toml": "[site]\nname = \"Epresso\"\nurl = \"https://example.com\"\n\n[build]\ntrailing_slash = \"always\"\n",
        "content.config.py": (
            "from pydantic import BaseModel\n"
            "from epresso.content import define_collection\n"
            "class Post(BaseModel):\n    title: str\n    date: str = ''\n"
            "posts = define_collection('posts', glob='*.md', base='./content/posts', schema=Post)\n"
        ),
        "content/posts/one.md": "---\ntitle: One\ndate: 2026-01-01\n---\n# One\n",
        "content/posts/two.md": "---\ntitle: Two\ndate: 2026-02-01\n---\n# Two\n",
        "templates/layouts/Base.ep": (
            "---\n"
            "---\n"
            "<!doctype html><html><head><title>{{ props.title }}</title></head>"
            "<body><slot/></body></html>\n"
        ),
    }


def test_epresso_route_static(tmp_path):
    files = _site_files()
    files["pages/about.ep"] = (
        "---\n"
        "---\n"
        "<Base title=\"About page\"><h1>About us</h1></Base>\n"
    )
    root, site = _make(files, tmp_path)
    site.build()
    html = (root / "dist" / "about" / "index.html").read_text()
    assert "<title>About page</title>" in html
    assert "<h1>About us</h1>" in html


def test_epresso_route_dynamic_with_get_static_paths(tmp_path):
    files = _site_files()
    files["pages/blog/index.ep"] = (
        "---\n"
        "---\n"
        "<Base title=\"Blog\"><ul>"
        "{% for p in site.get_collection('posts') %}<li>{{ p.data.title }}</li>{% endfor %}"
        "</ul></Base>\n"
    )
    files["pages/blog/[slug].ep"] = (
        "---\n"
        "from epresso.routing import Route\n"
        "def get_static_paths():\n"
        "    return [Route(path='/blog/'+p.id+'/', params={'slug': p.id}, data=p) for p in site.get_collection('posts')]\n"
        "---\n"
        "<Base title={props.title}><h1>{{ props.title }}</h1>{{ content|safe }}</Base>\n"
    )
    root, site = _make(files, tmp_path)
    site.build()
    html = (root / "dist" / "blog" / "one" / "index.html").read_text()
    assert "<h1>One</h1>" in html
    assert (root / "dist" / "blog" / "two" / "index.html").exists()


def test_epresso_component_with_props_validation(tmp_path):
    files = _site_files()
    files["templates/components/Card.ep"] = (
        "---\n"
        "from pydantic import BaseModel, Field\n"
        "class Props(BaseModel):\n"
        "    title: str\n"
        "    level: int = 3\n"
        "---\n"
        "<div class=\"card\"><h{{ props.level }}>{{ props.title }}</h{{ props.level }}>"
        "<div>{{ content }}</div></div>\n"
    )
    files["pages/index.ep"] = (
        "---\n"
        "---\n"
        "<Card title='Hi' level={2}>Body text</Card>\n"
    )
    root, site = _make(files, tmp_path)
    site.build()
    html = (root / "dist" / "index.html").read_text()
    assert "<h2>Hi</h2>" in html
    assert "Body text" in html


def test_epresso_component_props_validation_rejects_bad(tmp_path):
    files = _site_files()
    files["templates/components/Card.ep"] = (
        "---\n"
        "from pydantic import BaseModel\n"
        "class Props(BaseModel):\n"
        "    title: str\n"
        "---\n"
        "<div>{{ props.title }}</div>\n"
    )
    files["pages/index.ep"] = "---\n---\n<Card title={123}></Card>\n"
    root, site = _make(files, tmp_path)
    with pytest.raises(TemplateError, match="invalid props"):
        site.build()


def test_epresso_scoped_css(tmp_path):
    files = _site_files()
    files["templates/components/Button.ep"] = (
        "---\n"
        "---\n"
        "<style scoped>\n"
        "  .btn { color: red; }\n"
        "  .btn:hover { color: blue; }\n"
        "  :global(.raw) { margin: 0; }\n"
        "</style>\n"
        "<button class=\"btn\">{{ content }}</button>\n"
    )
    files["pages/index.ep"] = (
        "---\n"
        "---\n"
        "<Button>Go</Button>\n"
    )
    root, site = _make(files, tmp_path)
    site.build()
    index = (root / "dist" / "index.html").read_text()
    # component wrapped in scoping div + combined css link injected in head
    assert "data-epresso-" in index
    assert "_scoped/epresso." in index
    scoped = next((root / "dist" / "_scoped").rglob("*.css"))
    css = scoped.read_text()
    assert "[data-epresso-" in css
    assert ".btn" in css
    # :global rules are left unscoped (no data-epresso- prefix on the .raw selector)
    assert ".btn" in css
    assert "[data-epresso-" in css
    assert ".raw{" in css and ".raw[data-epresso-" not in css  # :global() stripped, unscoped


def test_epresso_route_scoped_css(tmp_path):
    files = _site_files()
    files["pages/feature.ep"] = (
        "---\n"
        "---\n"
        "<style scoped>\n"
        "  .feature { background: green; }\n"
        "</style>\n"
        "<section class=\"feature\">Featured</section>\n"
    )
    root, site = _make(files, tmp_path)
    site.build()
    html = (root / "dist" / "feature" / "index.html").read_text()
    assert "data-epresso-" in html
    assert "_scoped/epresso." in html


def test_scope_css_inserts_attribute_before_pseudo_elements():
    """Scoped selectors must put the attribute before pseudo- elements/classes,
    else rules like ``.x::before`` never match (a pseudo-element can't carry the
    attribute). Regression for broken line-number counters.
    """
    from epresso.scoped import scope_css

    css = (
        ".code-line::before { content: counter(line); }\n"
        ".btn:hover { color: blue; }\n"
        ".a, .b::after { x: y; }\n"
        ":global(.raw) { margin: 0; }\n"
    )
    out = scope_css(css, "abc123")
    assert ".code-line[data-epresso-abc123]::before" in out
    assert ".btn[data-epresso-abc123]:hover" in out
    assert ".a[data-epresso-abc123]" in out and ".b[data-epresso-abc123]::after" in out
    assert ".raw" in out and ".raw[data-epresso-abc123]" not in out  # :global() stripped, unscoped
    # the old (broken) behaviour — attribute after the pseudo-element
    assert ".code-line::before[data-epresso-abc123]" not in out


def test_component_is_global_style_renders_jinja_and_dedupes(tmp_path):
    """A component's ``<style is:global>`` is a Jinja template fragment: helpers
    like ``pygments_css()`` must render (not stay literal), and the inline
    ``<style>`` must be emitted once per page even when the component renders
    multiple times (e.g. one code block per Highlight).
    """
    files = _site_files()
    files["templates/components/Card.ep"] = (
        "---\n"
        "---\n"
        "<style is:global>{{ pygments_css('monokai', '.x') }}</style>\n"
        "<div class=\"card\">hello</div>\n"
    )
    files["pages/index.ep"] = (
        "---\n"
        "---\n"
        "<Card></Card>\n"
        "<Card></Card>\n"
    )
    root, site = _make(files, tmp_path)
    site.build()
    html = (root / "dist" / "index.html").read_text()
    # Jinja rendered inside the is:global style, not left as a literal tag
    assert "pygments_css" not in html
    assert ".x .k{color" in html  # monokai token rule rendered
    # deduped: the global <style> appears once despite two Card renders
    assert html.count("<style>") == 1


def test_epresso_loader_strips_empty_frontmatter_in_layout_component(tmp_path):
    """An empty-frontmatter page composing a layout component must not leak the
    ``---`` delimiters of either the page or the layout component into output.
    """
    files = _site_files()
    files["pages/about.ep"] = (
        "---\n"
        "---\n"
        "<Base title=\"About\"><h1>Hi</h1></Base>\n"
    )
    root, site = _make(files, tmp_path)
    site.build()
    html = (root / "dist" / "about" / "index.html").read_text()
    assert "<title>About</title>" in html
    assert "---" not in html  # no leaked frontmatter delimiters


def test_epresso_route_script_bundled_and_injected(tmp_path):
    files = _site_files()
    files["pages/feature.ep"] = (
        "---\n"
        "---\n"
        "<script>\n"
        "  import { greet } from './greet.js';\n"
        "  console.log(greet());\n"
        "</script>\n"
        "<section id=\"feat\">Featured</section>\n"
    )
    files["pages/greet.js"] = "export function greet(){ return 'hi'; }\n"
    root, site = _make(files, tmp_path)
    site.build()
    html = (root / "dist" / "feature" / "index.html").read_text()
    assert 'type="module"' in html
    assert "/_epresso/epresso." in html
    scripts = (root / "dist" / "_epresso")
    assert scripts.exists() and any(scripts.iterdir())


def test_epresso_component_script_registered(tmp_path):
    files = _site_files()
    files["templates/components/Badge.ep"] = (
        "---\n"
        "---\n"
        "<script>\n"
        "  document.documentElement.classList.add('has-badge');\n"
        "</script>\n"
        "<b class=\"badge\">{{ content }}</b>\n"
    )
    files["pages/index.ep"] = "---\n---\n<Badge>ok</Badge>\n"
    root, site = _make(files, tmp_path)
    site.build()
    html = (root / "dist" / "index.html").read_text()
    assert "/_epresso/epresso." in html
    assert 'type="module"' in html
