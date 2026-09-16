"""Docs theme keyboard-shortcuts overlay (`?`): rendered with the other
overlays, closed by default, and wired like the search overlay.

Component scripts are bundled (not inlined in the rendered page), so the wiring
is asserted against the component source.
"""

import re
from pathlib import Path

from epresso.site import Site

_THEME = Path(__file__).resolve().parents[2] / "themes" / "docs"
_SRC = (_THEME / "components" / "patterns" / "ShortcutsOverlay.ep").read_text(encoding="utf-8")


def _page(site: Site, path: str = "/basics/components/") -> str:
    html, ctype = site.render_at(path)
    assert ctype == "text/html"
    return html


def test_shortcuts_overlay_markup():
    html = _page(Site.load(_THEME))
    assert 'class="shortcuts-overlay" role="dialog" aria-modal="true"' in html
    assert 'aria-label="Keyboard shortcuts"' in html
    assert 'tabindex="-1"' in html
    # closed by default: the .open class is what reveals it
    assert "shortcuts-overlay open" not in html
    assert 'id="shortcuts-close"' in html
    # the documented keys
    for key in (">Ctrl/⌘</kbd>", ">K</kbd>", ">?</kbd>", ">[</kbd>", ">]</kbd>", ">,</kbd>", ">.</kbd>"):
        assert key in html, key
    # search-internal keys are not advertised here (they live in the search bar)
    assert ">Esc</kbd>" not in html
    assert "Move through search results" not in html
    # rendered by the layout, after the search overlay
    assert html.find('id="search-overlay"') < html.find('id="shortcuts-overlay"')
    # discoverable from the search hint bar
    assert re.search(r"<b[^>]*>\?</b> shortcuts", html)


def test_shortcuts_overlay_present_on_other_routes():
    assert 'id="shortcuts-overlay"' in _page(Site.load(_THEME), "/")


def test_shortcuts_overlay_owns_every_global_binding():
    """All global keys are bound here — one place for the modifier and
    "not while typing" rules — and broadcast to the owning component.

    Compared with every whitespace character stripped: the component script is
    bundled JS, not a fixed layout, and a formatter is free to re-wrap an object
    literal (or add/remove a space next to a brace) without changing what it
    does — collapsing runs of whitespace to one space still leaves that kind of
    diff visible, so this strips whitespace entirely instead.
    """
    squashed = re.sub(r"\s+", "", _SRC)
    # the documented keys, and nothing else
    for entry in (
        'code:"KeyK",mod:true,action:"search"',
        'code:"BracketLeft",run:function(){follow("data-pager-prev");}',
        'code:"BracketRight",run:function(){follow("data-pager-next");}',
        'code:"Comma",action:"section-prev"',
        'code:"Period",action:"section-next"',
    ):
        assert entry in squashed, entry
    assert 'newCustomEvent("epresso:shortcut",{detail:action})' in squashed
    # opens on a bare "?" (Shift+/ on most layouts) and toggles
    assert 'if(e.key==="?")' in squashed
    # bare keys are ignored while typing; modified ones (Ctrl/⌘K) are not
    assert "isTyping(e.target)" in squashed
    assert "if(!mod||e.altKey)continue;" in squashed
    # joins the one-panel-at-a-time protocol
    assert 'window.epressoPanelOpened("shortcuts")' in squashed
    assert 'e.detail!=="shortcuts"' in squashed
    # Escape and backdrop click close
    assert 'e.key==="Escape"' in squashed
    assert "e.target===overlay" in squashed


def test_pager_is_a_zero_js_component():
    """The pager only ever needed script for [ / ]: the overlay follows its
    links off the hooks it exposes, so it stays markup + CSS."""
    pager = (_THEME / "components" / "controls" / "Pager.ep").read_text(encoding="utf-8")
    assert "<script>" not in pager
    assert "data-pager-prev" in pager and "data-pager-next" in pager
    assert 'follow("data-pager-prev")' in _SRC  # the overlay does the work


def test_action_owners_keep_only_stateful_actions():
    """Search and the ToC keep an epresso:shortcut listener: their actions need
    state the overlay doesn't own (results/selection, current heading)."""
    theme = _THEME / "components"
    toc = (theme / "navigation" / "Toc.ep").read_text(encoding="utf-8")
    search = (theme / "patterns" / "SearchOverlay.ep").read_text(encoding="utf-8")
    assert 'if (e.detail === "search") open();' in search
    assert 'if (e.detail === "section-prev") jump(-1);' in toc
    assert 'else if (e.detail === "section-next") jump(1);' in toc
    assert "scrollIntoView(" in toc
    # neither binds the key itself any more
    assert 'addEventListener("keydown"' not in toc
    assert 'k.toLowerCase() === "k"' not in search
