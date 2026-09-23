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
            "components/Card.ep": (
                '---\nfrom pydantic import BaseModel\nclass Props(BaseModel):\n    title: str = ""\n---\n'
                '<div class="card"><h3>{{ props.title }}</h3>'
                "<header>{{ slot('header') }}</header>{{ content }}</div>"
            ),
            "pages/index.ep": '---\n---\n<Card title="Hi"><Fragment slot="header">HDR</Fragment>BODY</Card>',
        }
    )
    assert '<div class="card"><h3>Hi</h3><header>HDR</header>BODY</div>' in html
    assert "Fragment" not in html  # named-slot wrapper removed


def test_named_slot_fallback():
    html = _render(
        {
            "components/Badge.ep": "<b>{{ slot('x') or 'DEFAULT' }}</b>",
            "pages/index.ep": "---\n---\n<Badge>ignored</Badge>",
        }
    )
    assert "<b>DEFAULT</b>" in html


def test_style_is_global():
    html = _render(
        {
            "components/G.ep": (
                "---\n---\n"
                "<style>/* scoped */ .a { color: red; }</style>"
                "<style is:global>/* global */ .g { color: blue; }</style>"
                '<div class="a g">x</div>'
            ),
            "pages/index.ep": "---\n---\n<G />",
        }
    )
    # the <style is:global> block is emitted inline, unscoped (minified)
    assert "<style>.g{color:blue;}</style>" in html
    # the scoped <style> block is not inline (it's in the scoped bundle)
    assert ".a[" not in html
    # the scoped component still carries its scope attribute
    assert "data-epresso-" in html


def test_layout_with_global_style_is_not_scoped():
    # A layout shell emitting a full document is unscoped (no data-epresso wrapper);
    # an inline layout style is global via <style is:global>.
    html = _render(
        {
            "components/Layout.ep": (
                "---\n---\n"
                "<!doctype html><html><head><style is:global>.x{color:red}</style>"
                "<title>{{ title }}</title></head><body>{{ content }}</body></html>"
            ),
            "pages/index.ep": '---\n---\n<Layout title="T"><p>hello</p></Layout>',
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
            "components/Layout.ep": (
                "---\n---\n"
                "<!doctype html><html><head><style>.x{color:red}</style>"
                "<title>{{ title }}</title></head><body>{{ content }}</body></html>"
            ),
            "pages/index.ep": '---\n---\n<Layout title="T"><p>hello</p></Layout>',
        }
    )
    assert "data-epresso-" in html  # a scoped <style> opts the component into scoping


def test_scoped_component_still_scoped():
    # A normal (non-unscoped) .ep component keeps its data-epresso wrapper.
    html = _render(
        {
            "components/Btn.ep": ("---\n---\n<button>{{ content }}</button>\n<style>.b{color:blue}</style>"),
            "pages/index.ep": "---\n---\n<Btn>go</Btn>",
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
            "components/Card.ep": '<div class="card"><slot /></div>',
            "pages/index.ep": "---\n---\n<Card>BODY</Card>",
        }
    )
    assert '<div class="card">BODY</div>' in html
    assert "<slot" not in html


def test_slot_tag_named():
    """<slot name="X" /> renders the named slot; <slot /> the default."""
    html = _render(
        {
            "components/Layout.ep": (
                '---\n---\n<main><header><slot name="header" /></header><slot /></main>'
            ),
            "pages/index.ep": (
                '---\n---\n<Layout><Fragment slot="header">HDR</Fragment>BODY</Layout>'
            ),
        }
    )
    assert "<header>HDR</header>" in html
    assert ">BODY</main>" in html


def test_slot_tag_fallback():
    """<slot name="X">fallback</slot> shows fallback when the slot is empty."""
    html = _render(
        {
            "components/Badge.ep": '<b><slot name="x">DEFAULT</slot></b>',
            "pages/index.ep": "---\n---\n<Badge>ignored</Badge>",
        }
    )
    assert "<b>DEFAULT</b>" in html


def test_slot_tag_layout_as_component():
    """A layout component rendered as `<Page>` composes with slots."""
    html = _render(
        {
            "layouts/Page.ep": (
                "---\n---\n"
                '<!doctype html><html><head><title><slot name="title" /></title></head>'
                '<body><header><slot name="head" /></header><main><slot /></main></body></html>'
            ),
            "pages/index.ep": (
                "---\n---\n<Page>"
                '<Fragment slot="title">T</Fragment>'
                '<Fragment slot="head">NAV</Fragment>'
                "<h1>Body</h1>"
                "</Page>"
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
            "layouts/Page.ep": (
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


def test_slot_attribute_on_any_element():
    """slot="name" on a plain element slots the element itself (no wrapper)."""
    html = _render(
        {
            "components/Panel.ep": (
                '<div class="panel"><aside>{{ slot("side") }}</aside>'
                "<main>{{ content }}</main></div>"
            ),
            "pages/index.ep": '---\n---\n<Panel><img slot="side" src="/a.png" alt="a">MAIN</Panel>',
        }
    )
    assert '<aside><img src="/a.png" alt="a"></aside>' in html
    assert "slot=" not in html  # marker attribute is stripped
    assert "<main>MAIN</main>" in html


def test_slot_attribute_extracts_nested_subtree():
    html = _render(
        {
            "components/Panel.ep": '<div class="panel">{{ slot("side") }}{{ content }}</div>',
            "pages/index.ep": (
                '---\n---\n<Panel><section slot="side"><p>a</p><p>b</p></section>AFTER</Panel>'
            ),
        }
    )
    assert '<section><p>a</p><p>b</p></section>' in html
    assert "AFTER" in html
    assert "slot=" not in html


def test_data_slot_attribute_is_not_a_slot_marker():
    """`data-slot="…"` / `aria-slot="…"` are data attributes, not slot markers.

    `\b` alone matches between `-` and `slot`, so a prefixed attribute used to be
    extracted (and its element dropped); the marker regex now guards the prefix.
    """
    from epresso.components import _extract_slots

    content = '<div data-slot="track"><Inner /></div>'
    out, slots = _extract_slots(content)
    assert slots == {}
    assert out == content

    # A real `slot=` after a `data-slot=` still wins (it is not shadowed).
    out, slots = _extract_slots('<i data-slot="track" slot="side">x</i>')
    assert slots == {"side": '<i data-slot="track">x</i>'}
    assert out == ""


def test_component_inside_a_data_slot_element_renders():
    html = _render(
        {
            "components/Inner.ep": "---\n---\n<i>inner</i>",
            "components/Wrap.ep": '---\n---\n<div class="wrap"><slot /></div>',
            "pages/index.ep": '---\n---\n<Wrap><div data-slot="track"><Inner /></div></Wrap>',
        }
    )
    assert '<div class="wrap"><div data-slot="track"><i>inner</i></div></div>' in html


def test_slotless_fragment_renders_nothing():
    html = _render(
        {
            "components/Panel.ep": '<div class="panel">{{ content }}</div>',
            "pages/index.ep": "---\n---\n<Panel><Fragment><p>a</p><p>b</p></Fragment></Panel>",
        }
    )
    assert '<div class="panel"><p>a</p><p>b</p></div>' in html
    assert "Fragment" not in html


def test_shorthand_fragment_renders_nothing():
    html = _render(
        {
            "components/Panel.ep": '<div class="panel">{{ content }}</div>',
            "pages/index.ep": "---\n---\n<Panel><><p>a</p><p>b</p></></Panel>",
        }
    )
    assert '<div class="panel"><p>a</p><p>b</p></div>' in html
    assert "<>" not in html


def test_fragment_in_component_body_renders_nothing():
    html = _render(
        {
            "components/Wrap.ep": '<div class="wrap"><Fragment><i>a</i><i>b</i></Fragment></div>',
            "pages/index.ep": "---\n---\n<Wrap />",
        }
    )
    assert '<div class="wrap"><i>a</i><i>b</i></div>' in html
    assert "Fragment" not in html


def test_ep_file_shape_rejects_two_roots_at_build():
    import pytest

    from epresso.errors import TemplateError

    with pytest.raises(TemplateError) as exc:
        _render({"pages/index.ep": "---\n---\n<div>a</div><div>b</div>\n"})
    assert "invalid .ep file shape" in str(exc.value)


def test_extract_slots_fast_path_never_skips_a_marker():
    """`_extract_slots` skips the marker regex when the content has no `slot`
    literal. That regex costs ~6 ms on the 250 KB content string a layout gets
    (the lookbehind and the alternation are tried at every `<`), and on a 997-doc
    build none of its 30,744 calls was handed a marker — so the shortcut is where
    the time went.

    It is only safe if it is a superset of the real pattern, so assert both
    directions against that pattern: content it does not match comes back
    byte-identical (including when the cheap test over-triggers), and content it
    does match is still consumed by the slow path.
    """
    import re

    from epresso.components import _extract_slots

    marker = re.compile(r"<\s*/?\s*(?:>|fragment\b)|(?<![\w-])slot\s*=", re.IGNORECASE)
    cases = [
        '<Fragment slot="header">H</Fragment>BODY',
        "<Fragment>bare</Fragment>BODY",
        "<>grouped</>",
        "< div slot = 'side' >x</ div >",
        "<FRAGMENT>upper</FRAGMENT>BODY",
        # Over-trigger the cheap test: still must come back untouched.
        '<div data-slot="track"><Inner /></div>',
        "slotted text and <FragmentS>a</FragmentS>",
        "plain <p>content</p>",
    ]
    for content in cases:
        out, slots = _extract_slots(content)
        if marker.search(content) is None:
            assert (out, slots) == (content, {}), content
        else:
            assert out != content or slots, content



