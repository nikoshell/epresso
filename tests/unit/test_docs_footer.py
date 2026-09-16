"""Docs theme footer: an auto-fit grid (optional menu, optional build info)
above the credit line. The theme switch lives in the sidebar."""

import re
from pathlib import Path

from epresso.site import Site

_THEME = Path(__file__).resolve().parents[2] / "themes" / "docs"


def _footer(html: str) -> str:
    start = html.find('class="site-footer"')
    assert start != -1, "no footer rendered"
    return html[start : html.find("</footer>", start)]


def test_footer_grid_and_optional_menu():
    site = Site.load(_THEME)
    site.config.theme["footer"] = {
        "menu": [
            {"label": "Documentation", "href": "/"},
            {"label": "GitHub", "href": "https://github.com/nikoshell/epresso"},
        ]
    }
    footer = _footer(site.render_at("/basics/components/")[0])
    # the grid sits above the credit span
    assert 'class="footer-grid"' in footer
    assert footer.find('class="footer-grid"') < footer.find("Built with")
    # column 1: the menu from [theme.footer] menu (relative href through url())
    assert 'class="footer-col footer-menu"' in footer
    # the anchor is reflowed onto its own lines by `fmt --expand`, so match loosely
    assert re.search(r">\s*Documentation\s*</a>", footer)
    assert re.search(r'href="https://github\.com/nikoshell/epresso"[^>]*>\s*GitHub\s*</a>', footer)


def test_footer_menu_absent_when_not_configured():
    site = Site.load(_THEME)
    site.config.theme["footer"] = {}
    footer = _footer(site.render_at("/basics/components/")[0])
    assert "footer-menu" not in footer


def test_footer_debug_optional():
    site = Site.load(_THEME)
    site.config.theme["footer"] = {}
    assert "footer-debug" not in _footer(site.render_at("/basics/components/")[0])
    # `true` → env + epresso version; a table adds its own rows
    site.config.theme["footer"] = {"debug": {"commit": "a1b2c3d"}}
    footer = _footer(site.render_at("/basics/components/")[0])
    assert 'class="footer-col footer-debug"' in footer
    assert re.search(r"<dt[^>]*>commit</dt><dd[^>]*>a1b2c3d</dd>", footer)
    assert re.search(r"<dt[^>]*>env</dt>", footer) and re.search(r"<dt[^>]*>epresso</dt>", footer)
    assert re.search(r"<dt[^>]*>epresso</dt><dd[^>]*>\d+\.\d+", footer)
