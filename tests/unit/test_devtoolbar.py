"""Tests for the dev toolbar (injected only by the dev server)."""

import re
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


def test_toolbar_persists_open_and_hidden_state():
    """The open panel and the hidden state live in the toolbar prefs (localStorage),
    so a reload or a dev-server restart restores them instead of resetting."""
    site = _site()
    out = devtoolbar.inject(_page(site, "/basics/components/"), site, "/basics/components/")
    # the open panel is remembered in prefs, not sessionStorage
    assert "prefs.app=app;savePrefs();" in out
    assert "prefs.app='';savePrefs();" in out
    assert "__epresso_app" not in out
    # hidden state is persisted and restored on load (hidden wins over open)
    assert "prefs.hidden=!!hidden;savePrefs();" in out
    assert "if(prefs.hidden){setHidden(true);}" in out
    assert "else if(prefs.app&&prefs.app!=='inspect'" in out
    assert "if(dismiss)dismiss.onclick=function(){setHidden(true);};" in out


def test_theme_emulation_button():
    """A toolbar button fakes the OS colour-scheme preference."""
    site = _site()
    out = devtoolbar.inject(_page(site, "/basics/components/"), site, "/basics/components/")
    m = re.search(r'<button[^>]*id="__epresso_tb_theme"[^>]*>', out)
    assert m, "theme button missing"
    # a panel app would carry data-app and be handled by the app switcher
    assert "data-app" not in m.group(0)
    # cycles system -> dark -> light, remembered in the toolbar prefs
    assert "['system','dark','light']" in out
    assert "prefs.theme=" in out
    # pins the palette itself: data-theme drives color-scheme, so every
    # light-dark() on the page (tokens and code palette) follows
    assert "root.setAttribute('data-theme',mode)" in out
    assert "root.removeAttribute('data-theme')" in out


def test_keyboard_shortcuts_wired():
    """Shift+Alt+D toggles the toolbar, Shift+Alt+I the inspect mode."""
    site = _site()
    out = devtoolbar.inject(_page(site, "/basics/components/"), site, "/basics/components/")
    # the handler: bare Shift+Alt, matched on e.code (layout independent)
    assert "if(!e.shiftKey||!e.altKey||e.ctrlKey||e.metaKey)return;" in out
    assert "var keys={KeyD:toggleToolbar,KeyI:toggleInspect,KeyL:toggleLayout};" in out
    # never while typing
    assert "isContentEditable" in out
    # toggleToolbar flips the persisted hidden state; hiding also closes the
    # panel / exits inspect
    assert "function toggleToolbar(){setHidden(tb.style.display!=='none');}" in out
    assert "if(prefs.hidden){close();deactivateInspect();if(pop)pop.hidden=true;clearOutline();tb.style.display='none';}" in out
    # advertised on the controls and in the settings panel
    assert 'title="Inspect elements (Shift+Alt+I)"' in out
    assert 'title="Hide toolbar (Shift+Alt+D)"' in out
    assert "Shift</kbd>+<kbd>Alt</kbd>+<kbd>D</kbd>" in out
