"""Redirects (Option C) and Pygments syntax highlighting tests."""

from pathlib import Path

import pytest

from epresso.config import Config
from epresso.markdown import pygments_css, render_markdown
from epresso.site import Site


def _make(files, tmp_path):
    root = Path(tmp_path)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root, Site.load(root)


# --- redirects Option C -------------------------------------------------------
def test_redirect_routes_string_and_status(tmp_path):
    files = {
        "site.toml": (
            "[site]\nname = \"T\"\nurl = \"https://example.com\"\n\n"
            "[[redirects]]\n\"/old/\" = \"/new/\"\n\n"
            "[[redirects]]\n\"/temp/\" = { destination = \"/now/\", status = 302 }\n"
        ),
        "pages/index.html": "index",
    }
    root, site = _make(files, tmp_path)
    site.build()
    old = (root / "dist" / "old" / "index.html").read_text()
    assert "url=/new/" in old
    assert "data-epresso-status='301'" in old
    temp = (root / "dist" / "temp" / "index.html").read_text()
    assert "url=/now/" in temp
    assert "data-epresso-status='302'" in temp


def test_redirect_routes_resolve_from_config(tmp_path):
    files = {"site.toml": "[[redirects]]\n\"/a/\" = \"/b/\"\n"}
    root, site = _make(files, tmp_path)
    routes = [r for r in site.resolve_routes() if "data-epresso-status" in (r.body or "")]
    assert len(routes) == 1
    assert routes[0].path == "/a/"


def test_build_redirects_toggle_off(tmp_path):
    files = {
        "site.toml": (
            "[build]\nredirects = false\n\n"
            "[[redirects]]\n\"/a/\" = \"/b/\"\n"
        ),
        "pages/index.html": "index",
    }
    root, site = _make(files, tmp_path)
    site.build()
    assert not (root / "dist" / "a" / "index.html").exists()


def test_invalid_redirect_target_rejected():
    with pytest.raises(Exception, match="redirect target"):
        Config(redirects=[{"/a/": {"no_destination": 1}}])


# --- Pygments syntax highlighting ---------------------------------------------
def test_markdown_highlights_fenced_code(tmp_path):
    md_config = type("MC", (), {"highlight": True})()
    body = "```python\nprint('hi')\n```"
    out = render_markdown(body, md_config)
    assert '<pre class="highlight"><code class="language-python">' in out.html
    # Pygments emits a span for the string token
    assert '<span' in out.html


def test_markdown_highlight_disabled(tmp_path):
    md_config = type("MC", (), {"highlight": False})()
    out = render_markdown("```python\nprint('hi')\n```", md_config)
    assert '<span' not in out.html
    assert "language-python" in out.html


def test_markdown_unknown_language_plain(tmp_path):
    md_config = type("MC", (), {"highlight": True})()
    out = render_markdown("```definitelynotalang\nfoo\n```", md_config)
    assert '<span' not in out.html
    assert "definitelynotalang" in out.html


def test_markdown_highlights_epresso_code(tmp_path):
    md_config = type("MC", (), {"highlight": True})()
    body = "```epresso\n---\nclass Props(BaseModel):\n    pass\n---\n<div>{{ x }}</div>\n```"
    out = render_markdown(body, md_config)
    assert 'class="language-epresso"' in out.html
    assert '<span class="k">' in out.html  # Python keyword token
    assert '<span class="nt">' in out.html  # HTML tag token


def test_epresso_lexer_frontmatter_delimiters():
    from pygments.token import Comment

    from epresso.highlight import EpressoLexer

    code = "---\nclass P: pass\n---\n<div>{{ x }}</div>"
    toks = list(EpressoLexer().get_tokens_unprocessed(code))
    # Both the opening and closing `---` delimiters are Comment, not Python operators.
    dashes = [t for t in toks if t[2] == "---\n"]
    assert len(dashes) == 2
    assert all(t[1] is Comment for t in dashes)
    # No text is lost or duplicated.
    assert "".join(t[2] for t in toks) == code


def test_pygments_css_helper():
    css = pygments_css()
    assert ".highlight" in css
