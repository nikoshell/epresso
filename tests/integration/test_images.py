"""Image service tests (require Pillow)."""

import pytest

from epresso.site import Site

pil = pytest.importorskip("PIL")


def _make(files):
    import tempfile
    from pathlib import Path

    d = tempfile.mkdtemp()
    root = Path(d)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")
    return root, Site.load(root)


def _png(width=100, height=60):
    import io

    from PIL import Image

    im = Image.new("RGB", (width, height), (200, 30, 40))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def test_image_renders_srcset_and_builds_webp(tmp_path):
    root, site = _make(
        {
            "assets/photos/hero.png": _png(1200, 600),
            "pages/index.ep": (
                "---\n---\n{{ image('photos/hero.png', widths=[400,800,1200], alt='Hero') }}"
            ),
        }
    )
    site.build()
    out = site.config.dir_output()
    # webp variants generated
    files = sorted(p.name for p in out.joinpath("images").rglob("hero-*.webp"))
    assert len(files) == 3
    html = (out / "index.html").read_text()
    assert "srcset=" in html
    assert "400w" in html and "1200w" in html
    assert "alt=\"Hero\"" in html


def test_image_fallback_when_source_missing(tmp_path):
    root, site = _make({"pages/index.ep": "---\n---\nx"})
    tag = site.images.render("nope.jpg", alt="x")
    assert tag.startswith("<img")


def test_image_passthrough_without_pillow(tmp_path, monkeypatch):
    root, site = _make({"assets/img/a.png": _png()})
    monkeypatch.setattr("epresso.images._has_pillow", lambda: False)
    tag = site.images.render("img/a.png", alt="a")
    assert "/assets/img/a.png" in tag
    assert "srcset=" not in tag
