"""Docs theme page actions: a "Copy page" button plus a "More options" menu.

On by default; `[theme] page_actions = false` turns the control off and stops the
per-page `<page>.md` routes it links to. The menu is a native `<details>`
disclosure, so its links work with JS off; only the copy action needs script.
"""

import re
from pathlib import Path

from epresso.site import Site

_THEME = Path(__file__).resolve().parents[2] / "themes" / "docs"
_SRC = (_THEME / "components" / "controls" / "PageActions.ep").read_text(encoding="utf-8")


def _flat(s: str) -> str:
    """Collapse whitespace so CSS assertions don't depend on formatter indentation."""
    return re.sub(r"\s+", " ", s)


def _site(*, enabled: bool = True) -> Site:
    """A docs site with the option set explicitly (its default is on)."""
    site = Site.load(_THEME)
    site.config.theme["page_actions"] = enabled
    return site


def _block(site: Site, path: str = "/basics/components/") -> str:
    html, _ = site.render_at(path)
    start = html.find('class="page-actions"')
    assert start != -1, "page actions missing"
    return html[start : html.find('<article class="doc"')]


def _md_routes(site: Site) -> set[str]:
    return {r.path for r in site.resolve_routes() if r.path.endswith(".md")}


def test_on_by_default():
    site = Site.load(_THEME)  # no [theme] override
    assert "/basics/components.md" in _md_routes(site)
    assert 'id="page-menu"' in _block(site)


def test_disabled_via_theme_option():
    site = _site(enabled=False)
    assert _md_routes(site) == set()
    html, _ = site.render_at("/basics/components/")
    assert "page-actions" not in html
    assert "page-menu" not in html


def test_markdown_sibling_route_is_emitted():
    site = _site()
    md = _md_routes(site)
    assert "/basics/components.md" in md
    route = next(r for r in site.resolve_routes() if r.path == "/basics/components.md")
    assert route.body and route.body.lstrip().startswith("# Components")
    assert route.content_type.startswith("text/markdown")
    # body-less hubs get no markdown sibling (nothing to serve)
    assert "/index.md" not in md


def test_copy_button_offers_markdown():
    block = _block(_site())
    assert 'id="page-copy"' in block
    assert 'aria-label="Copy page"' in block
    assert 'data-md="/basics/components.md"' in block
    assert "pa-icon--copy" in block and "pa-icon--check" in block


def test_more_options_menu_items():
    block = _block(_site())
    assert 'id="page-menu"' in block
    assert 'aria-label="More options"' in block
    # five entries, each a label + a subtitle
    assert block.count('class="pa-item-label"') == 5
    assert block.count('class="pa-hint"') == 5
    for label in (
        "Copy page",
        "Copy this page as Markdown",
        "View as Markdown",
        "Open this page as plain Markdown",
        "View source of this page",
        "Open in ChatGPT",
        "Open in Claude",
    ):
        assert label in block, label
    assert block.count("Ask questions about this page") == 2
    # the markdown link targets the page's .md sibling
    assert block.count('href="/basics/components.md"') == 1
    # AI links carry the absolute markdown URL
    assert "https://chatgpt.com/?q=Read%20https%3A//epresso.top/basics/components.md" in block
    assert "https://claude.ai/new?q=Read%20https%3A//epresso.top/basics/components.md" in block
    # the source link points at the file, with the path as its subtitle
    assert "View source of this page" in block
    assert "docs/basics/components.md" in block
    assert 'href="https://github.com/nikoshell/epresso/blob/main/docs/basics/components.md"' in block
    # no separator, and no edit link
    assert "pa-sep" not in block
    assert "Edit this page" not in block


def test_menu_is_a_native_disclosure_so_links_survive_without_js():
    block = _block(_site())
    assert "<details" in block and "<summary" in block


def test_source_item_needs_a_repository():
    site = _site()
    site.config.site.repository = ""
    block = _block(site)
    assert 'id="page-menu"' in block
    assert "View as Markdown" in block
    assert "View source of this page" not in block


def test_solo_group_when_no_markdown():
    # A page rendered without a markdown sibling (e.g. a non-docs page using
    # this component) gets one rounded button and no menu.
    assert "pa-group{% if not props.markdown %} pa-group--solo{% endif %}" in _SRC
    assert "{% if props.markdown %}" in _SRC
    assert ".pa-group--solo .pa-copy" in _SRC


def test_hover_states_are_not_invisible():
    """--surface and --bg are ~1% apart in light mode: hover must not swap
    between them (that made menu/button hovers invisible)."""
    assert ".pa-btn:hover { background: var(--accent-soft);" in _flat(_SRC)
    assert ".pa-item:hover { background: var(--accent-soft);" in _flat(_SRC)
    assert "background: var(--bg);" not in _SRC


def test_control_hovers_use_a_visible_fill():
    """Same fix for the other controls that sit on --surface."""
    theme = _THEME / "components"
    for rel in (
        "primitives/IconButton.ep",
        "controls/SidebarToggle.ep",
        "structure/Header.ep",
        "patterns/ShortcutsOverlay.ep",
    ):
        src = (theme / rel).read_text(encoding="utf-8")
        assert "background: var(--accent-soft);" in src, rel
        assert "background: var(--bg);" not in src.split(":hover")[1][:200], rel


def test_copy_wiring():
    """Copy = fetch the static .md sibling, then the clipboard; the "Copied"
    state is CSS (.is-done), not text written from JS."""
    assert 'var md = btn.getAttribute("data-md");' in _SRC
    assert "fetch(md)" in _SRC
    assert "navigator.clipboard.writeText(text)" in _SRC
    assert 'btn.classList.add("is-done")' in _SRC
    assert ".pa-copy.is-done .pa-label-copied" in _SRC
    # no DOM-derived fallback: the markdown is a static file, not re-derived
    assert "cloneNode" not in _SRC
    assert "pageText" not in _SRC
    assert 'id="page-copy-md"' in _SRC
    # menu closes on outside click / Escape / choosing an item
    assert 'e.key === "Escape" && menu.open' in _SRC
    assert "!menu.contains(e.target)" in _SRC
    assert 'e.target.closest("a, button")' in _SRC
