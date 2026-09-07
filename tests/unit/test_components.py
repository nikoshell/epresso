"""Component system (`{% component %}`) tests."""

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
            "templates/components/Card.html": (
                "<div class=\"card\"><h3>{{ title }}</h3><p>{{ content }}</p>"
                "<span>{{ site.config.site.name }}</span></div>\n"
            ),
            "pages/index.html": (
                "{% component \"Card\", title=\"Hi\", url=\"/x/\" %}"
                "Body <strong>text</strong>"
                "{% endcomponent %}\n"
            ),
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
            "templates/components/Badge.html": "<b>{{ content or '—' }}</b>",
            "pages/index.html": '{% component "Badge" %}{% endcomponent %}',
        }
    )
    site.build()
    assert "<b>—</b>" in (site.config.dir_output() / "index.html").read_text()


def test_missing_component_raises(tmp_path):
    root, site = _make({"pages/index.html": '{% component "Nope" %}{% endcomponent %}'})
    try:
        site.build()
        raise AssertionError("expected TemplateError")
    except TemplateError as e:
        assert "Nope" in str(e)
