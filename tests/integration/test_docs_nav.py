"""docs.toml `nav`, `redirects`, `extra_css` and the key allowlist."""

import re

from typer.testing import CliRunner

from epresso.cli import app

runner = CliRunner()


def _site(tmp_path, toml: str):
    d = tmp_path / "docs"
    (d / "guide").mkdir(parents=True)
    (d / "index.md").write_text("# Home\n\nhi\n", encoding="utf-8")
    (d / "guide" / "install.md").write_text("# Install\n\ni\n", encoding="utf-8")
    (d / "guide" / "usage.md").write_text("# Usage\n\nu\n", encoding="utf-8")
    (d / "secret.md").write_text("# Secret\n\ns\n", encoding="utf-8")
    (tmp_path / "extra.css").write_text(".x{}", encoding="utf-8")
    (tmp_path / "docs.toml").write_text(toml, encoding="utf-8")
    return tmp_path


def test_nav_orders_groups_hides_and_links(tmp_path, monkeypatch):
    _site(
        tmp_path,
        'extra_css = ["extra.css"]\n'
        'redirects = [{"/old/" = "/guide/usage/"}]\n'
        "[[sources]]\n"
        'source = "docs"\n'
        'nav = ["index.md", {"Start" = [{"Use it" = "guide/usage.md"}, "guide/install.md"]},'
        ' {"GitHub" = "https://github.com/x/y"}]\n',
    )
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"
    result = runner.invoke(app, ["docs", ".", "--out", str(out)])
    assert result.exit_code == 0, result.output
    page = (out / "guide" / "usage" / "index.html").read_text(encoding="utf-8")
    nav = page[page.index('id="sidebar-nav"') :]
    # nav order, section label, title override, external link; unlisted page hidden
    assert re.search(r"Start.*Use it.*Install.*GitHub", nav, re.S)
    assert 'href="https://github.com/x/y"' in nav
    assert "Secret" not in nav
    assert (out / "secret" / "index.html").exists()  # still built
    assert "/docs-extra/extra.css" in page and (out / "docs-extra" / "extra.css").exists()
    assert (out / "old" / "index.html").exists()


def test_unknown_docs_toml_key_is_an_error(tmp_path, monkeypatch):
    _site(tmp_path, 'colour = "red"\n')
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["docs", ".", "--out", str(tmp_path / "out")])
    assert result.exit_code != 0
    assert "colour" in result.output
