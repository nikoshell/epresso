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
