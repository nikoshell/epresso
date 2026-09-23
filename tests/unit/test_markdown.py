"""Markdown rendering + AST metadata (headings, image paths) tests."""

from epresso.markdown import render_markdown


def _cfg():
    return type("M", (), {"toc_heading": None, "add_slug_ids": True, "autolink_headings": True})()


def test_renders_html():
    r = render_markdown("# Hello\n\n**bold** text.", _cfg())
    assert "<h1 id=\"hello\">" in r.html
    assert 'href="#hello"' in r.html  # heading anchor link
    assert "<strong>bold</strong>" in r.html


def test_headings_extracted_with_slugs():
    r = render_markdown("# One\n\n## Two Words\n\n### Three\n", _cfg())
    assert r.metadata["headings"] == [
        {"depth": 1, "slug": "one", "text": "One"},
        {"depth": 2, "slug": "two-words", "text": "Two Words"},
        {"depth": 3, "slug": "three", "text": "Three"},
    ]


def test_image_paths_extracted():
    md = "![alt](/img/a.jpg)\n\n![x](hero.png)\n"
    r = render_markdown(md, _cfg())
    assert "/img/a.jpg" in r.metadata["image_paths"]
    assert "hero.png" in r.metadata["image_paths"]


def test_empty_body():
    r = render_markdown("", _cfg())
    assert r.html == ""
    assert r.metadata["headings"] == []


def test_rendered_content_fields():
    r = render_markdown("# T\n", _cfg())
    assert hasattr(r, "html")
    assert isinstance(r.metadata["image_paths"], list)


def test_code_component_per_language_routing():
    from epresso.markdown import render_markdown

    cfg = type(
        "M",
        (),
        {
            "toc_heading": None,
            "add_slug_ids": True,
            "autolink_headings": True,
            "highlight": True,
            "code_component": "Highlight",
            "code_components": {"tree": "Tree"},
        },
    )()
    # tree block routes to the per-language Tree component
    tree = render_markdown("```tree\ncontent/\n  posts/\n    a.md\n```\n", cfg)
    assert "Tree" in tree.html and "content/" in tree.html
    # default language still routes to the default Highlight component
    py = render_markdown("```python\nx = 1\n```\n", cfg)
    assert "Highlight" in py.html


def test_rust_backend_reports_unavailable():
    """Selecting an uninstalled backend fails loudly, it does not fall back."""
    from epresso.config import MarkdownConfig
    from epresso.errors import ContentError

    try:
        render_markdown("# x\n", MarkdownConfig(backend="rust"))
    except ContentError as e:
        assert "rust" in str(e)
    else:
        raise AssertionError("expected ContentError for an uninstalled backend")


def test_body_is_parsed_once_per_render(monkeypatch):
    """Headings/images come from the render's token stream, not a second parse."""
    from markdown_it import MarkdownIt

    calls = {"n": 0}
    original = MarkdownIt.parse

    def counting(self, src, env=None):
        calls["n"] += 1
        return original(self, src, env)

    monkeypatch.setattr(MarkdownIt, "parse", counting)
    r = render_markdown("# One\n\n## Two\n\n![i](./a.png)\n", _cfg())
    assert calls["n"] == 1
    assert [h["slug"] for h in r.metadata["headings"]] == ["one", "two"]
    assert r.metadata["image_paths"] == ["./a.png"]
