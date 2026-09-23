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


def test_nav_collapse_threshold_is_the_theme_option():
    """`[theme] nav_collapse_after` (default 40) decides when the top level folds.
    The body reads it and passes it in, so this component's frontmatter stays
    render-independent (it is executed once per environment, not per page)."""
    from epresso.site import Site

    site = Site.load(_THEME)
    site.config.theme["nav_collapse_after"] = 10_000  # never fold
    expanded, _ = site.render_at("/basics/components/")
    assert 'class="tree-head"' in expanded
    site.config.theme["nav_collapse_after"] = 1  # fold immediately
    folded, _ = site.render_at("/basics/components/")
    assert 'class="tree-head"' not in folded
    assert "<summary" in folded


def test_sidebar_is_rendered_once_and_marked_client_side():
    """The tree is identical on every page, so it is rendered once per build
    (`_NAV_CACHE`) and must carry no per-page state; the current page is marked
    by the component's script. Re-adding a server-side marker would silently
    invalidate the cache for every page, so assert the split."""
    assert "def render_sidebar(docs, collapse_after=None)" in _SRC  # no per-page `current`
    assert "_NAV_CACHE[key] = hit" in _SRC
    frontmatter_and_markup = _SRC.split("<script>")[0]
    assert "aria-current" not in frontmatter_and_markup
    assert '<details open>' not in frontmatter_and_markup
    # the script relies on these hooks to find and mark the current page
    assert "markCurrent" in _SRC
    assert 'link.setAttribute("aria-current", "page")' in _SRC
    assert 'el.classList.contains("tree-dir")' in _SRC

