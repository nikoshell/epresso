"""Tests for the dev toolbar (injected only by the dev server)."""

from pathlib import Path

from epresso import devtoolbar
from epresso.site import Site

_REPO = Path(__file__).resolve().parents[2]


def _site() -> Site:
    return Site.load(_REPO / "themes" / "docs")


def _page(site: Site, path: str) -> str:
    html, ct = site.render_at(path)
    assert ct == "text/html"
    return html


def test_toolbar_injected_for_html_page():
    site = _site()
    html = _page(site, "/basics/components/")
    out = devtoolbar.inject(html, site, "/basics/components/")
    assert "__epresso_toolbar" in out
    assert "/basics/components/" in out


def test_toolbar_disabled_is_noop():
    site = _site()
    html = _page(site, "/basics/components/")
    site.config.dev.toolbar.enabled = False
    assert "__epresso_toolbar" not in devtoolbar.inject(html, site, "/basics/components/")


def test_toolbar_not_injected_in_production_env():
    # `epresso docs` / `epresso preview` default to the production env: the dev
    # toolbar must not be served into a production build.
    site = Site.load(_REPO / "themes" / "docs", env="production")
    html = "<html><body>x</body></html>"
    assert devtoolbar.inject(html, site, "/") == html
    assert "__epresso_toolbar" not in devtoolbar.inject(html, site, "/")


def test_never_injects_without_body():
    site = _site()
    assert devtoolbar.inject("<p>no body tag</p>", site, "/x/") == "<p>no body tag</p>"


def test_page_panel_lists_content_for_a_content_page():
    site = _site()
    site.render_at("/basics/components/")  # populate dependency edges for this path
    panel = devtoolbar._page_panel(site, "/basics/components/")
    assert "docs" in panel
    assert "basics/components" in panel


def test_page_panel_no_content_dependencies():
    site = _site()
    panel = devtoolbar._page_panel(site, "/no-such-route/")
    assert "no content dependencies" in panel
