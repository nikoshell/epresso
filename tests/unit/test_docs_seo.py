"""The docs theme emits canonical + Open Graph + Twitter tags via ``seo()``.

``Base.ep`` composes them from the ``title``/``path`` props that ``Doc`` passes
down from each page's route, so a deep page is canonical to its own URL.
"""

from __future__ import annotations

from pathlib import Path

from epresso.site import Site

_THEME = Path(__file__).resolve().parents[2] / "themes" / "docs"
_SITE_URL = "https://epresso.top/"


def _render(path: str) -> str:
    site = Site.load(_THEME)
    html, _ = site.render_at(path)
    return html


def test_deep_page_head_tags():
    html = _render("/basics/components/")
    assert f'<link rel="canonical" href="{_SITE_URL}basics/components/"' in html
    assert 'property="og:title" content="Components · epresso"' in html
    assert 'property="og:type" content="website"' in html
    assert f'property="og:url" content="{_SITE_URL}basics/components/"' in html
    assert f'property="og:image" content="{_SITE_URL}epresso.png"' in html
    assert 'name="twitter:card" content="summary_large_image"' in html


def test_home_page_head_tags():
    html = _render("/")
    assert f'<link rel="canonical" href="{_SITE_URL}"' in html
    assert 'property="og:title" content="epresso"' in html
    assert 'name="twitter:title" content="epresso"' in html


def test_404_page_has_its_own_title_and_canonical():
    html = _render("/404/")
    assert 'property="og:title" content="404 · epresso"' in html
    assert f'<link rel="canonical" href="{_SITE_URL}404/"' in html
