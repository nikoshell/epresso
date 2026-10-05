"""epresso_social: og:image social cards per section / page / collection."""

import re

import pytest

from epresso.config import load_config
from epresso.site import Site

pytest.importorskip("PIL")


def _site(tmp_path, cards: str | None = None, extra: str = ""):
    (tmp_path / "content" / "posts").mkdir(parents=True)
    (tmp_path / "pages" / "guides").mkdir(parents=True)
    opts = f'cards = "{cards}"\n' if cards else ""
    (tmp_path / "site.toml").write_text(
        'plugins = ["epresso_social"]\n[site]\nname = "Acme"\nurl = "https://acme.dev/"\n'
        'description = "Acme docs"\n'
        f"[plugin.epresso_social]\n{opts}{extra}",
        encoding="utf-8",
    )
    page = '---\ntitle = "{t}"\n---\n<html><head><title>{t} · Acme</title><meta name="description" content="{d}"></head><body>x</body></html>\n'
    (tmp_path / "pages" / "index.ep").write_text(page.format(t="Home", d="hi"), encoding="utf-8")
    (tmp_path / "pages" / "guides" / "index.ep").write_text(page.format(t="All the guides", d="read"), encoding="utf-8")
    (tmp_path / "pages" / "guides" / "install.ep").write_text(page.format(t="Install", d="i"), encoding="utf-8")
    (tmp_path / "pages" / "own.ep").write_text(
        '<html><head><title>Own</title><meta property="og:image" content="https://x/y.png"></head><body/></html>\n',
        encoding="utf-8",
    )
    site = Site(load_config(tmp_path))
    site.build()
    return tmp_path / "dist"


def _og(out, rel):
    m = re.search(r'property="og:image" content="([^"]+)"', (out / rel).read_text(encoding="utf-8"))
    return m.group(1) if m else None


def test_sections_default(tmp_path):
    out = _site(tmp_path)
    assert _og(out, "index.html") == "https://acme.dev/social/site.png"
    assert _og(out, "guides/index.html") == _og(out, "guides/install/index.html") == "https://acme.dev/social/guides.png"
    assert _og(out, "own/index.html") == "https://x/y.png"  # own image kept
    assert sorted(p.name for p in (out / "social").iterdir()) == ["guides.png", "site.png"]
    from PIL import Image

    assert Image.open(out / "social" / "guides.png").size == (1200, 630)
    assert 'name="twitter:card" content="summary_large_image"' in (out / "index.html").read_text(encoding="utf-8")


def test_all_mode_one_card_per_page(tmp_path):
    out = _site(tmp_path, "all")
    assert _og(out, "guides/install/index.html") == "https://acme.dev/social/guides--install.png"
    assert len(list((out / "social").iterdir())) == 3


def test_long_title_still_draws(tmp_path):
    import sys

    sys.path.insert(0, str(__import__("epresso").plugins._BUNDLED_PLUGINS))
    from epresso_social import draw_card

    png = draw_card("word " * 60, "desc " * 80, "Acme", {}, tmp_path)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_bad_mode_is_an_error(tmp_path):
    with pytest.raises(Exception, match="cards"):
        _site(tmp_path, "weird")
