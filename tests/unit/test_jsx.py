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
            "templates/components/Feature.html": '<section class="feature">{{ layout }}</section>',
            "pages/index.html": '<Feature layout="three-column" />',
        }
    )
    assert '<section class="feature">three-column</section>' in html


def test_expression_and_boolean_attrs():
    html = _render(
        {
            "templates/components/Toggle.html": "<b>{{ on and 'ON' or 'OFF' }}|{{ enabled }}</b>",
            "pages/index.html": "<Toggle on={True} enabled />",
        }
    )
    assert "<b>ON|True</b>" in html


def test_paired_component_with_children():
    html = _render(
        {
            "templates/components/Card.html": '<div class="card"><h3>{{ title }}</h3>{{ content }}</div>',
            "pages/index.html": '<Card title="Hi">Hello <strong>world</strong></Card>',
        }
    )
    assert '<div class="card"><h3>Hi</h3>Hello <strong>world</strong></div>' in html


def test_nested_components_in_children():
    html = _render(
        {
            "templates/components/Inner.html": "<i>inner</i>",
            "templates/components/Card.html": '<div class="card">{{ content }}</div>',
            "pages/index.html": "<Card title=\"x\"><Inner /></Card>",
        }
    )
    assert '<div class="card"><i>inner</i></div>' in html


def test_plain_html_and_jinja_left_untouched():
    html = _render(
        {
            "templates/components/Hero.html": '<section class="hero">{{ content }}</section>',
            "pages/index.html": (
                '<main><Hero /></main>\n'
                '{% set x = "<Hero/>" %}<div>{{ x }}</div>\n'
                '<script>const s = "<Hero/>";</script>'
            ),
        }
    )
    # <main> is plain HTML; <Hero /> became a component.
    assert "<main><section class=\"hero\"></section></main>" in html
    # The string inside the {% set %} was NOT turned into a component — it
    # stayed a plain (autoescaped) string value when printed.
    assert "&lt;Hero/&gt;" in html
    # The <script> body is untouched (not converted to a component).
    assert '<script>const s = "<Hero/>";</script>' in html


def test_legacy_component_tag_still_works_alongside():
    html = _render(
        {
            "templates/components/A.html": "<a>A</a>",
            "templates/components/B.html": "<b>{{ content }}</b>",
            "pages/index.html": '<A />{% component "B" %}legacy{% endcomponent %}',
        }
    )
    assert "<a>A</a>" in html
    assert "<b>legacy</b>" in html


def test_epresso_component_with_props_model():
    html = _render(
        {
            "templates/components/Heading.ep": (
                "---\nfrom pydantic import BaseModel\n"
                "class Props(BaseModel):\n    level: int = 2\n    text: str = \"\"\n---\n"
                "<h{{ props.level }}>{{ props.text }}</h{{ props.level }}>\n"
            ),
            "pages/index.html": '<Heading level={3} text="Hello" />',
        }
    )
    assert "<h3>Hello</h3>" in html


def test_inline_component_children_with_jinja():
    """Inline <Component>children</Component> containing Jinja rewrites correctly
    (regression: the JSX rewrite used to skip tags whose children had {{ }}/{% %})."""
    html = _render(
        {
            "templates/components/Card.ep": '<div class="card">{{ content }}</div>',
            "pages/index.html": (
                "<Card><a href=\"{{ url('/x') }}\">L</a>{% for i in [1,2] %}<b>{{ i }}</b>{% endfor %}</Card>"
            ),
        }
    )
    assert '<div class="card"><a href="/x/">L</a><b>1</b><b>2</b></div>' in html
