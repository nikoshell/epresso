"""Docs theme sidebar: the tree's scroll area fades its scrolled-away edges.

`--scroll-area-overflow-y-start/-end` are page-set custom properties (Base UI /
shadcn convention) — the mask's gradient stops are `min(fade-size, overflow)`,
so an edge only fades while there is content beyond it.
"""

from pathlib import Path

_THEME = Path(__file__).resolve().parents[2] / "themes" / "docs"
_SRC = (_THEME / "components" / "navigation" / "NavAccordion.ep").read_text(encoding="utf-8")


def test_label_only_rows_do_not_hover():
    """A top-level group whose hub has no page renders as <div class=tree-head>
    <span>Label</span></div> — not a link, so hovering it must not highlight."""
    assert ".tree-top>.tree-head:has(> a):hover:not(.active)" in _SRC


def test_sidebar_hover_matches_between_themes():
    """The row hover is a theme-matched step from the page background, not a
    fixed dark hex (that was a subtle lift on dark but a heavy box on light).
    The row text follows the theme too — a fixed #fff vanished on the light
    fill."""
    assert "--tree-row-hover: light-dark(#eeeeee, #1a1d23);" in _SRC
    assert "color: #fff;" not in _SRC


def test_nav_mask_fades_both_edges():
    assert "--scroll-area-fade-size: 1.5rem;" in _SRC
    assert "mask-image: linear-gradient(" in _SRC
    assert "min(var(--scroll-area-fade-size), var(--scroll-area-overflow-y-start, 0px))" in _SRC
    assert "min(var(--scroll-area-fade-size), var(--scroll-area-overflow-y-end, 0px))" in _SRC


def test_nav_mask_overflow_is_published_by_the_script():
    assert "__epressoSidebarFade" in _SRC
    assert 'style.setProperty("--scroll-area-overflow-y-start", top + "px")' in _SRC
    assert 'style.setProperty("--scroll-area-overflow-y-end", (max - top) + "px")' in _SRC
    # recomputed when the amount of scrollable content can change
    assert 'fadeNav.addEventListener("scroll", publishFades' in _SRC
    assert 'window.addEventListener("resize", publishFades)' in _SRC
    assert 'document.addEventListener("toggle", publishFades, true)' in _SRC

