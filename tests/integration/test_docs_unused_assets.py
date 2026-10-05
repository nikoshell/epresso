"""epresso_docs ships only the source files something links to."""

from typer.testing import CliRunner

from epresso.cli import app


def test_unreferenced_source_files_are_left_out(tmp_path):
    src = tmp_path / "proj"
    (src / "docs" / "img").mkdir(parents=True)
    for name in ("used.png", "unused.png", "my pic.png", "linked.zip", "raw.png"):
        (src / "docs" / "img" / name).write_bytes(b"x")
    (src / "README.md").write_text("# Home\n\nhi\n", encoding="utf-8")
    (src / "docs" / "guide").mkdir()
    (src / "docs" / "guide" / "deep.md").write_text("# Deep\n\n![c](../img/up.png)\n", encoding="utf-8")
    (src / "docs" / "img" / "up.png").write_bytes(b"x")
    (src / "docs" / "page.md").write_text(
        "# Page\n\n![a](img/used.png)\n\n![b](<img/my pic.png>)\n\n[download](img/linked.zip)\n\n<img src=\"../img/raw.png\" alt=\"raw\">\n", encoding="utf-8"
    )
    out = tmp_path / "out"
    result = CliRunner().invoke(app, ["docs", str(src), "--out", str(out)])
    assert result.exit_code == 0, result.output
    shipped = {p.name for p in out.rglob("*") if p.is_file()}
    assert {"used.png", "my pic.png", "up.png", "linked.zip", "raw.png"} <= shipped
    assert "unused.png" not in shipped


def test_links_resolve_like_mkdocs(tmp_path):
    """Markdown URLs resolve against the file's dir; raw-HTML URLs against the
    page URL (one level deeper for non-index pages), like a browser on MkDocs."""
    src = tmp_path / "proj"
    (src / "docs" / "guide").mkdir(parents=True)
    (src / "docs" / "assets").mkdir()
    (src / "docs" / "assets" / "a.png").write_bytes(b"x")
    (src / "docs" / "assets" / "f.pdf").write_bytes(b"x")
    (src / "README.md").write_text("# Home\n\nhi\n", encoding="utf-8")
    (src / "docs" / "guide" / "p.md").write_text(
        '# P\n\n![md](../assets/a.png)\n\n<img src="../../assets/a.png" alt="raw">\n\n[pdf](../assets/f.pdf)\n',
        encoding="utf-8",
    )
    out = tmp_path / "out"
    assert CliRunner().invoke(app, ["docs", str(src), "--out", str(out)]).exit_code == 0
    import re

    html = (out / "guide" / "p" / "index.html").read_text(encoding="utf-8")
    urls = re.findall(r'(?:src|href)="(/[^"]*(?:a\.png|f\.pdf))"', html)
    assert len(urls) >= 3 and len(set(urls)) == 2, urls  # md + raw img → same file
    for u in set(urls):
        assert (out / u.lstrip("/")).is_file(), u
