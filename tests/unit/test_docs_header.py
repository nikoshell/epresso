"""Docs theme header: the GitHub icon (right of the theme toggle) links to the
site repository and is rendered only when a repository is configured."""

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
    # .header-actions right cluster: search, then theme toggle, then GitHub
    assert (
        html.find("search-open")
        < html.find("theme-toggle")
        < html.find('aria-label="GitHub repository"')
    )


def test_header_hides_github_link_when_no_repository():
    site = Site.load(_REPO / "themes" / "docs")
    site.config.site.repository = ""
    html, _ = site.render_at("/basics/components/")
    assert _github_anchor(html) is None
