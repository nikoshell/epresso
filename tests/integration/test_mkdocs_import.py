"""mkdocs.yml → docs.toml (`epresso import mkdocs`) and live `epresso docs`."""

import tomllib

from typer.testing import CliRunner

from epresso.cli import app
from epresso.mkdocs_import import mkdocs_to_docs_config

runner = CliRunner()

MKDOCS = """\
site_name: Demo
site_url: https://demo.dev/
repo_url: https://github.com/o/demo
docs_dir: docs
theme:
  name: material
  palette: {primary: indigo}
nav:
  - Home: index.md
  - Guide:
      - guide/install.md
markdown_extensions:
  - admonition
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
  - pymdownx.arithmatex
plugins:
  - search
  - social
  - redirects:
      redirect_maps:
        old.md: guide/install.md
extra_css:
  - css/extra.css
"""


def _project(tmp_path):
    (tmp_path / "docs" / "guide").mkdir(parents=True)
    (tmp_path / "docs" / "css").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n\nhi\n", encoding="utf-8")
    (tmp_path / "docs" / "guide" / "install.md").write_text("# Install\n\ni\n", encoding="utf-8")
    (tmp_path / "docs" / "css" / "extra.css").write_text(".x{}", encoding="utf-8")
    (tmp_path / "mkdocs.yml").write_text(MKDOCS, encoding="utf-8")
    return tmp_path


def test_mapping_and_warnings(tmp_path):
    cfg, warn = mkdocs_to_docs_config(_project(tmp_path) / "mkdocs.yml")
    assert cfg["title"] == "Demo"
    assert cfg["site"] == {"url": "https://demo.dev/", "repository": "https://github.com/o/demo"}
    assert cfg["sources"][0]["nav"][1] == {"Guide": ["guide/install.md"]}
    assert cfg["sources"][0]["repo_url"] == "https://github.com/o/demo/blob/main/docs"
    assert cfg["redirects"] == [{"/old/": "/guide/install/"}]
    assert cfg["extra_css"] == ["docs/css/extra.css"]
    text = "\n".join(warn)
    assert "pymdownx.emoji" in text and "arithmatex" in text and "theme" in text
    assert "admonition" not in text and "search" not in text and "social" not in text


def test_import_writes_docs_toml_and_refuses_overwrite(tmp_path, monkeypatch):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["import", "mkdocs"]).exit_code == 0
    cfg = tomllib.loads((tmp_path / "docs.toml").read_text(encoding="utf-8"))
    assert cfg["title"] == "Demo" and cfg["sources"][0]["source"] == "docs"
    again = runner.invoke(app, ["import", "mkdocs"])
    assert again.exit_code == 1 and "--force" in again.output
    assert runner.invoke(app, ["import", "mkdocs", "--force"]).exit_code == 0


def test_live_and_imported_builds_match(tmp_path, monkeypatch):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    live = runner.invoke(app, ["docs", ".", "--out", str(tmp_path / "live")])
    assert live.exit_code == 0, live.output
    runner.invoke(app, ["import", "mkdocs"])
    imported = runner.invoke(app, ["docs", ".", "--out", str(tmp_path / "imp")])
    assert imported.exit_code == 0, imported.output
    assert "mkdocs.yml ignored" in imported.output
    for rel in ("index.html", "guide/install/index.html", "old/index.html", "docs-extra/extra.css"):
        assert (tmp_path / "live" / rel).exists() and (tmp_path / "imp" / rel).exists(), rel
