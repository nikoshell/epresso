"""JSX-style component-tag syntax tests (``<Header />`` etc.)."""

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


def _render(files):
    _root, site = _make(files)
    site.build()
    return (site.config.dir_output() / "index.html").read_text()


def test_self_closing_tag_with_string_attr():
    html = _render(
        {
            "components/Feature.ep": '---\n---\n<section class="feature">{{ layout }}</section>',
            "pages/index.ep": '---\n---\n<Feature layout="three-column" />',
        }
    )
    assert '<section class="feature">three-column</section>' in html


def test_expression_and_boolean_attrs():
    html = _render(
        {
            "components/Toggle.ep": "---\n---\n<b>{{ on and 'ON' or 'OFF' }}|{{ enabled }}</b>",
            "pages/index.ep": "---\n---\n<Toggle on={True} enabled />",
        }
    )
    assert "<b>ON|True</b>" in html


def test_paired_component_with_children():
    html = _render(
        {
            "components/Card.ep": '---\n---\n<div class="card"><h3>{{ title }}</h3>{{ content }}</div>',
            "pages/index.ep": '---\n---\n<Card title="Hi">Hello <strong>world</strong></Card>',
        }
    )
    assert '<div class="card"><h3>Hi</h3>Hello <strong>world</strong></div>' in html


def test_nested_components_in_children():
    html = _render(
        {
            "components/Inner.ep": "---\n---\n<i>inner</i>",
            "components/Card.ep": '---\n---\n<div class="card">{{ content }}</div>',
            "pages/index.ep": "---\n---\n<Card title=\"x\"><Inner /></Card>",
        }
    )
    assert '<div class="card"><i>inner</i></div>' in html


def test_plain_html_and_jinja_left_untouched():
    _root, site = _make(
        {
            "components/Hero.ep": '---\n---\n<section class="hero">{{ content }}</section>',
        }
    )
    site._do_load()
    html = site.env.from_string(
        '<main><Hero /></main>\n'
        '{% set x = "<Hero/>" %}<div>{{ x }}</div>\n'
        '<script>const s = "<Hero/>";</script>'
    ).render({})
    # <main> is plain HTML; <Hero /> became a component.
    assert "<main><section class=\"hero\"></section></main>" in html
    # The string inside the {% set %} was NOT turned into a component — it
    # stayed a plain (autoescaped) string value when printed.
    assert "&lt;Hero/&gt;" in html
    # The <script> body is untouched (not converted to a component).
    assert '<script>const s = "<Hero/>";</script>' in html


def test_legacy_component_tag_still_works_alongside():
    _root, site = _make(
        {
            "components/A.ep": "---\n---\n<a>A</a>",
            "components/B.ep": "---\n---\n<b>{{ content }}</b>",
        }
    )
    site._do_load()
    html = site.env.from_string('<A />{% component "B" %}legacy{% endcomponent %}').render({})
    assert "<a>A</a>" in html
    assert "<b>legacy</b>" in html


def test_epresso_component_with_props_model():
    html = _render(
        {
            "components/Heading.ep": (
                "---\nfrom pydantic import BaseModel\n"
                "class Props(BaseModel):\n    level: int = 2\n    text: str = \"\"\n---\n"
                "<h{{ props.level }}>{{ props.text }}</h{{ props.level }}>\n"
            ),
            "pages/index.ep": '---\n---\n<Heading level={3} text="Hello" />',
        }
    )
    assert "<h3>Hello</h3>" in html


def test_inline_component_children_with_jinja():
    """Inline <Component>children</Component> containing Jinja rewrites correctly
    (regression: the JSX rewrite used to skip tags whose children had {{ }}/{% %})."""
    html = _render(
        {
            "components/Card.ep": '<div class="card">{{ content }}</div>',
            "pages/index.ep": (
                "---\n---\n<Card><a href=\"{{ url('/x') }}\">L</a>{% for i in [1,2] %}<b>{{ i }}</b>{% endfor %}</Card>"
            ),
        }
    )
    assert '<div class="card"><a href="/x/">L</a><b>1</b><b>2</b></div>' in html


def test_namespace_qualified_tag_disambiguates_duplicate_basenames():
    """<A:comp1 /> / <A:comp2 /> resolve to components/comp1/A.ep and
    components/comp2/A.ep deterministically -- unlike bare <A /> resolution,
    which is undefined when a basename exists in more than one subdirectory."""
    html = _render(
        {
            "components/comp1/A.ep": '---\n---\n<span>from comp1</span>\n',
            "components/comp2/A.ep": '---\n---\n<span>from comp2</span>\n',
            "pages/index.ep": "---\n---\n<Fragment><A:comp1 /> <A:comp2 /></Fragment>",
        }
    )
    assert "<span>from comp1</span>" in html
    assert "<span>from comp2</span>" in html


def test_namespace_qualified_components_scope_css_independently():
    """Two files sharing a basename must not collide on scoped CSS (the scope
    hash is keyed on the call name, e.g. "A:comp1" vs "A:comp2", not the file's
    bare stem)."""
    import re

    html = _render(
        {
            "components/comp1/A.ep": (
                '---\n---\n<div class="box">one</div>\n<style>.box{color:red}</style>\n'
            ),
            "components/comp2/A.ep": (
                '---\n---\n<div class="box">two</div>\n<style>.box{color:blue}</style>\n'
            ),
            "pages/index.ep": "---\n---\n<Fragment><A:comp1 /> <A:comp2 /></Fragment>",
        }
    )
    hashes = set(re.findall(r"data-epresso-([a-z0-9]+)", html))
    assert len(hashes) == 2
