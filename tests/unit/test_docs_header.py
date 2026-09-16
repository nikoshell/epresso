"""Docs theme header: the GitHub icon links to the site repository and is
rendered only when a repository is configured."""

import re
from pathlib import Path

from epresso.site import Site

_REPO = Path(__file__).resolve().parents[2]
_REPO_URL = "https://github.com/nikoshell/epresso"


def _github_anchor(html: str) -> str | None:
    m = re.search(r'<a [^>]*aria-label="GitHub repository"[^>]*>', html)
    return m.group(0) if m else None


def test_header_github_link_present_when_repository_set():
    site = Site.load(_REPO / "themes" / "docs")
    html, ctype = site.render_at("/basics/components/")
    assert ctype == "text/html"
    anchor = _github_anchor(html)
    assert anchor is not None
    assert f'href="{_REPO_URL}"' in anchor
    assert 'target="_blank" rel="noopener noreferrer"' in anchor
    assert "{{" not in anchor  # href must be resolved, not a literal template tag
    # .header-actions right cluster: search, then GitHub
    assert html.find("search-open") < html.find('aria-label="GitHub repository"')


def test_colour_scheme_needs_no_script():
    """No switcher and no theme script: color-scheme follows the OS, and every
    colour (design tokens and code palette alike) is a light-dark() pair."""
    site = Site.load(_REPO / "themes" / "docs")
    html, _ = site.render_at("/basics/components/")
    assert "theme-switch" not in html
    assert "ThemeToggle" not in html
    assert 'class="doc-foot"' not in html
    # nothing publishes data-theme any more
    assert 'setAttribute("data-theme"' not in html
    assert "data-theme-mode" not in html
    assert "localStorage" not in html
    # the palette rides on color-scheme instead: the theme pairs the two
    # Pygments palettes into one stylesheet (asserted against its source, since
    # component CSS is bundled rather than inlined in the page)
    highlight = (_REPO / "themes" / "docs" / "components" / "patterns" / "Highlight.ep").read_text(encoding="utf-8")
    assert "pygments_css_pair(" in highlight
    assert 'html[data-theme="dark"]' not in highlight


def test_only_the_dev_toolbar_pins_the_palette():
    """data-theme is an override hook: it exists so the toolbar can pin
    color-scheme; the stylesheet is where it is honoured."""
    css = (_REPO / "themes" / "docs" / "styles" / "global.css").read_text(encoding="utf-8")
    assert 'html[data-theme="light"] {\n  color-scheme: light;' in css
    assert 'html[data-theme="dark"] {\n  color-scheme: dark;' in css
    assert ":root {\n  color-scheme: light dark;" in css


def test_header_hides_github_link_when_no_repository():
    site = Site.load(_REPO / "themes" / "docs")
    site.config.site.repository = ""
    html, _ = site.render_at("/basics/components/")
    assert _github_anchor(html) is None
