"""Named slots (``<Fragment slot=…>``) and layout component behavior."""

from epresso.site import Site


def _render(files):
    import tempfile
    from pathlib import Path

    d = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    site = Site.load(d)
    site.build()
    return (site.config.dir_output() / "index.html").read_text()


def test_named_slot_epresso():
    html = _render(
        {
            "templates/components/Card.ep": (
                '---\nfrom pydantic import BaseModel\nclass Props(BaseModel):\n    title: str = ""\n---\n'
                '<div class="card"><h3>{{ props.title }}</h3>'
                "<header>{{ slot('header') }}</header>{{ content }}</div>"
            ),
            "pages/index.html": ('<Card title="Hi"><Fragment slot="header">HDR</Fragment>BODY</Card>'),
        }
    )
    assert '<div class="card"><h3>Hi</h3><header>HDR</header>BODY</div>' in html
    assert "Fragment" not in html  # named-slot wrapper removed


def test_named_slot_fallback():
    html = _render(
        {
            "templates/components/Badge.ep": "<b>{{ slot('x') or 'DEFAULT' }}</b>",
            "pages/index.html": "<Badge>ignored</Badge>",
        }
    )
    assert "<b>DEFAULT</b>" in html


def test_style_is_global():
    html = _render(
        {
            "templates/components/G.ep": (
                "---\n---\n"
                "<style>/* scoped */ .a { color: red; }</style>"
                "<style is:global>/* global */ .g { color: blue; }</style>"
                '<div class="a g">x</div>'
            ),
            "pages/index.html": "<G />",
        }
    )
    # the <style is:global> block is emitted inline, unscoped (minified)
    assert "<style>.g{color:blue;}</style>" in html
    # the scoped <style> block is not inline (it's in the scoped bundle)
    assert ".a[" not in html
    # the scoped component still carries its scope attribute
    assert "data-epresso-" in html


def test_named_slot_html_component():
    html = _render(
        {
            "templates/components/Panel.html": (
                '<div class="panel"><aside>{{ slot("side") }}</aside>{{ content }}</div>'
            ),
            "pages/index.html": '<Panel><Fragment slot="side">S</Fragment>main</Panel>',
        }
    )
    assert '<div class="panel"><aside>S</aside>main</div>' in html


def test_layout_with_global_style_is_not_scoped():
    # A layout shell emitting a full document is unscoped (no data-epresso wrapper);
    # an inline layout style is global via <style is:global>.
    html = _render(
        {
            "templates/components/Layout.ep": (
                "---\n---\n"
                "<!doctype html><html><head><style is:global>.x{color:red}</style>"
                "<title>{{ title }}</title></head><body>{{ content }}</body></html>"
            ),
            "pages/index.html": '<Layout title="T"><p>hello</p></Layout>',
        }
    )
    assert "data-epresso-" not in html  # no scoped wrapper around the document
    assert "<title>T</title>" in html
    assert "<style>.x{color:red}</style>" in html  # global style, emitted inline
    assert "<p>hello</p>" in html


def test_layout_with_scoped_style_is_scoped():
    # A component with a plain <style> is scoped (wrapped + selector rewritten).
    html = _render(
        {
            "templates/components/Layout.ep": (
                "---\n---\n"
                "<!doctype html><html><head><style>.x{color:red}</style>"
                "<title>{{ title }}</title></head><body>{{ content }}</body></html>"
            ),
            "pages/index.html": '<Layout title="T"><p>hello</p></Layout>',
        }
    )
    assert "data-epresso-" in html  # a scoped <style> opts the component into scoping


def test_scoped_component_still_scoped():
    # A normal (non-unscoped) .ep component keeps its data-epresso wrapper.
    html = _render(
        {
            "templates/components/Btn.ep": ("---\n---\n<button>{{ content }}</button>\n<style>.b{color:blue}</style>"),
            "pages/index.html": "<Btn>go</Btn>",
        }
    )
    assert "data-epresso-" in html
    # the scope attribute is injected onto the element itself,
    # not wrapped in a <div data-epresso-*>
    assert "<button " in html and "data-epresso-" in html
    assert ">go</button>" in html


def test_slot_tag_default():
    """<slot /> renders the default slot (children)."""
    html = _render(
        {
            "templates/components/Card.ep": '<div class="card"><slot /></div>',
            "pages/index.html": "<Card>BODY</Card>",
        }
    )
    assert '<div class="card">BODY</div>' in html
    assert "<slot" not in html


def test_slot_tag_named():
    """<slot name="X" /> renders the named slot; <slot /> the default."""
    html = _render(
        {
            "templates/components/Layout.ep": (
                '---\n---\n<main><header><slot name="header" /></header><slot /></main>'
            ),
            "pages/index.html": (
                '{% component "Layout" %}<Fragment slot="header">HDR</Fragment>BODY{% endcomponent %}'
            ),
        }
    )
    assert "<header>HDR</header>" in html
    assert ">BODY</main>" in html


def test_slot_tag_fallback():
    """<slot name="X">fallback</slot> shows fallback when the slot is empty."""
    html = _render(
        {
            "templates/components/Badge.ep": '<b><slot name="x">DEFAULT</slot></b>',
            "pages/index.html": "<Badge>ignored</Badge>",
        }
    )
    assert "<b>DEFAULT</b>" in html


def test_slot_tag_layout_as_component():
    """A layout rendered via {% component %} composes with slots."""
    html = _render(
        {
            "templates/layouts/Page.ep": (
                "---\n---\n"
                '<!doctype html><html><head><title><slot name="title" /></title></head>'
                '<body><header><slot name="head" /></header><main><slot /></main></body></html>'
            ),
            "pages/index.html": (
                '{% component "Page" %}'
                '<Fragment slot="title">T</Fragment>'
                '<Fragment slot="head">NAV</Fragment>'
                "<h1>Body</h1>"
                "{% endcomponent %}"
            ),
        }
    )
    assert "<title>T</title>" in html
    assert "<header>NAV</header>" in html
    assert "<main><h1>Body</h1></main>" in html


def test_extract_slots_preserves_interleaved_content():
    """Default content between named fragments is kept (regression)."""
    from epresso.components import _extract_slots

    content = '<Fragment slot="a">A</Fragment>MIDDLE<Fragment slot="b">B</Fragment>END'
    c, slots = _extract_slots(content)
    assert c == "MIDDLEEND"
    assert slots == {"a": "A", "b": "B"}


def test_markdown_page_slot_layout():
    """A direct Markdown page with a slot-based layout composes via {% component %}."""
    html = _render(
        {
            "templates/layouts/Page.ep": (
                '---\nfrom pydantic import BaseModel\nclass Props(BaseModel):\n    title: str = ""\n---\n'
                '<!doctype html><html><head><title><slot name="title" /></title></head>'
                "<body><main><slot /></main></body></html>"
            ),
            "pages/index.md": "---\nlayout: Page\ntitle: About\n---\n# Heading\n\nBody text.",
        }
    )
    assert "<title>About</title>" in html
    assert "<h1" in html and "Heading" in html
    assert "Body text." in html
