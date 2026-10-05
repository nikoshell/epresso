"""epresso_optimize: content <img> → WebP srcset + lazy + intrinsic size."""

import re

import pytest
from typer.testing import CliRunner

from epresso.cli import app

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

runner = CliRunner()


def test_docs_images_get_srcset(tmp_path):
    src = tmp_path / "proj"
    (src / "docs" / "img").mkdir(parents=True)
    Image.new("RGB", (2000, 1000), "red").save(src / "docs" / "img" / "big.png")
    Image.new("RGB", (300, 150), "blue").save(src / "docs" / "img" / "small.jpg")
    (src / "README.md").write_text("# Home\n\nhi\n", encoding="utf-8")
    (src / "docs" / "page.md").write_text(
        "# Page\n\n![big](img/big.png)\n\n![small](img/small.jpg)\n\n"
        '<img src="img/big.png" width="10" alt="kept">\n\n![ext](https://x.dev/a.png)\n',
        encoding="utf-8",
    )
    out = tmp_path / "out"
    result = runner.invoke(app, ["docs", str(src), "--out", str(out)])
    assert result.exit_code == 0, result.output
    html = (out / "page" / "index.html").read_text(encoding="utf-8")
    imgs = re.findall(r"<img\b[^>]*>", html[html.index('<article class="doc"') :])
    big = next(i for i in imgs if 'alt="big"' in i)
    for w in (400, 800, 1200):
        assert f" {w}w" in big
    assert 'width="2000" height="1000"' in big and 'loading="lazy"' in big
    assert 'sizes="(max-width: 46rem) 100vw, 46rem"' in big
    assert "big.png" in re.search(r'\ssrc="([^"]+)"', big).group(1)  # original stays the fallback
    small = next(i for i in imgs if 'alt="small"' in i)
    assert " 300w" in small and " 400w" not in small  # never upscaled
    kept = next(i for i in imgs if 'alt="kept"' in i)
    assert "srcset" not in kept
    ext = next(i for i in imgs if 'alt="ext"' in i)
    assert "srcset" not in ext
    webps = list((out / "images").glob("big-*.webp"))
    assert len(webps) == 3 and all(p.stat().st_size > 0 for p in webps)
    assert Image.open(sorted(webps, key=lambda p: p.stat().st_size)[0]).size == (400, 200)
