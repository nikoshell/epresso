"""Component system tests — components, props, and the `{% component %}` tag."""

from epresso.errors import TemplateError
from epresso.site import Site


def _make(files):
    import tempfile
    from pathlib import Path

    d = tempfile.mkdtemp()
    root = Path(d)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root, Site.load(root)


def test_component_renders_kwargs_content_and_site(tmp_path):
    root, site = _make(
        {
            "components/Card.ep": (
                "---\n---\n"
                "<div class=\"card\"><h3>{{ title }}</h3><p>{{ content }}</p>"
                "<span>{{ site.config.site.name }}</span></div>\n"
            ),
            "pages/index.ep": '---\n---\n<Card title="Hi" url="/x/">Body <strong>text</strong></Card>\n',
        }
    )
    site.build()
    html = (site.config.dir_output() / "index.html").read_text()
    assert "<h3>Hi</h3>" in html
    assert "Body <strong>text</strong>" in html
    assert "My Site" in html


def test_self_closing_component_empty_content(tmp_path):
    root, site = _make(
        {
            "components/Badge.ep": "---\n---\n<b>{{ content or '—' }}</b>",
            "pages/index.ep": '---\n---\n<Badge />',
        }
    )
    site.build()
    assert "<b>—</b>" in (site.config.dir_output() / "index.html").read_text()


def test_missing_component_raises(tmp_path):
    root, site = _make({})
    site._do_load()
    try:
        site.env.from_string('{% component "Nope" %}{% endcomponent %}').render({})
        raise AssertionError("expected TemplateError")
    except TemplateError as e:
        assert "Nope" in str(e)


_TONE_EP = (
    "---\n"
    "from typing import Literal\n"
    "\n"
    "from pydantic import BaseModel\n"
    "\n"
    "TONES = {'info': 'text-info', 'error': 'text-error'}\n"
    "\n"
    "\n"
    "class Props(BaseModel):\n"
    "    tone: Literal[*TONES] = 'info'\n"
    "---\n"
    '<span class="{{ TONES[props.tone] }}">{{ content }}</span>\n'
)


def test_props_annotation_resolves_non_builtin_types(tmp_path):
    """Frontmatter is compiled with ``dont_inherit=True``.

    This module has ``from __future__ import annotations``, and without the flag
    that future is inherited by user frontmatter: every ``Props`` annotation is
    stored as a string, and pydantic has no module to resolve it against (the
    namespace is just a plain dict), so anything but a builtin failed with
    ``Props is not fully defined``. ``Literal[…]`` must keep working.
    """
    root, site = _make(
        {
            "components/Tone.ep": _TONE_EP,
            "pages/index.ep": '---\n---\n<Tone tone="error">x</Tone>\n',
        }
    )
    site.build()
    html = (site.config.dir_output() / "index.html").read_text()
    assert 'class="text-error"' in html


def test_props_literal_rejects_an_unknown_value(tmp_path):
    """A ``Literal[*TABLE]`` prop turns a typo into a build-time props error
    (named component included) instead of a render-time KeyError."""
    root, site = _make(
        {
            "components/Tone.ep": _TONE_EP,
            "pages/index.ep": '---\n---\n<Tone tone="typo">x</Tone>\n',
        }
    )
    try:
        site.build()
        raise AssertionError("expected TemplateError")
    except TemplateError as e:
        msg = str(e)
        assert "invalid props for component 'Tone'" in msg
        assert "tone" in msg


def test_component_css_template_compiled_once(monkeypatch):
    """A component's <style> is compiled at parse time, not on every render."""
    import jinja2

    root, site = _make(
        {
            "components/Box.ep": (
                "---\n---\n"
                '<div class="box"><slot/></div>\n'
                "<style>.box { color: red }</style>\n"
            ),
            "pages/index.ep": '---\n---\n<div><Box>a</Box><Box>b</Box></div>\n',
        }
    )
    compiled: list[str] = []
    original = jinja2.Environment.from_string

    def counting(self, source, globals=None, template_class=None):
        compiled.append(source)
        return original(self, source, globals, template_class)

    monkeypatch.setattr(jinja2.Environment, "from_string", counting)
    site.build()
    # Two Box renders, but its stylesheet source was compiled only once.
    assert [s for s in compiled if ".box" in s and "color: red" in s] == [
        ".box { color: red }"
    ]
    # ...and both renders still produced scoped markup.
    html = (site.config.dir_output() / "index.html").read_text()
    assert html.count("class=\"box\"") == 2


def test_render_independent_frontmatter_is_executed_once(tmp_path):
    """Frontmatter that never reads site/props is executed at parse time.

    Otherwise every render re-runs its module body — e.g. Icon.ep rebuilt its
    whole icon dict 3,919 times in a real docs build.
    """
    from epresso.components import _parse_component

    root, site = _make(
        {
            "components/Static.ep": "---\nVALUE = 41 + 1\n---\n<p>{{ VALUE }}</p>\n",
            "components/Dynamic.ep": '---\nVALUE = props.get("n", 0)\n---\n<p>{{ VALUE }}</p>\n',
            "pages/index.ep": '---\n---\n<div><Static /><Dynamic n={2} /></div>\n',
        }
    )
    site._do_load()
    static_ns = _parse_component(root / "components" / "Static.ep", site.env)[9]
    dynamic_ns = _parse_component(root / "components" / "Dynamic.ep", site.env)[9]
    assert static_ns is not None and static_ns["VALUE"] == 42
    assert dynamic_ns is None  # reads props -> must run per render

    site.build()
    html = (site.config.dir_output() / "index.html").read_text()
    assert ">42<" in html and ">2<" in html
