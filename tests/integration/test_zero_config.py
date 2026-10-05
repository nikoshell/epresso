"""Zero-config `epresso docs <dir>` and the plain `epresso docs` example."""

from typer.testing import CliRunner

from epresso.cli import app

runner = CliRunner()


def _docs(tmp_path, files: dict[str, str]):
    src = tmp_path / "proj"
    for rel, text in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_text(text, encoding="utf-8")
    src.mkdir(exist_ok=True)
    out = tmp_path / "out"
    result = runner.invoke(app, ["docs", str(src), "--out", str(out)])
    assert result.exit_code == 0, result.output
    return result, out


def test_readme_and_docs(tmp_path):
    result, out = _docs(tmp_path, {"README.md": "# My Proj\n\nhello\n", "docs/install.md": "# Install\n\ni\n",
                                   "notes.md": "# Loose\n\nnot docs\n"})
    assert "hello" in (out / "index.html").read_text(encoding="utf-8")
    assert (out / "install" / "index.html").exists()
    assert not (out / "notes").exists()  # only docs/ + README
    assert "no docs/" not in result.output


def test_readme_only_warns_about_docs(tmp_path):
    result, out = _docs(tmp_path, {"README.md": "# Solo\n\nonly me\n"})
    assert "only me" in (out / "index.html").read_text(encoding="utf-8")
    assert "no docs/" in result.output


def test_readme_wins_over_docs_index(tmp_path):
    result, out = _docs(tmp_path, {"README.md": "# R\n\nfrom readme\n", "docs/index.md": "# I\n\nfrom index\n",
                                   "docs/a.md": "# A\n\na\n"})
    assert "from readme" in (out / "index.html").read_text(encoding="utf-8")
    assert "README.md is the homepage" in result.output


def test_placeholder_without_readme(tmp_path):
    result, out = _docs(tmp_path, {"docs/a.md": "# A\n\na\n"})
    home = (out / "index.html").read_text(encoding="utf-8")
    assert "README.md" in home and "docs/" in home
    assert "placeholder" in result.output


def test_empty_dir_gets_placeholder(tmp_path):
    result, out = _docs(tmp_path, {})
    assert "README.md" in (out / "index.html").read_text(encoding="utf-8")


def test_plain_docs_is_epresso_docs_and_hints_projects(tmp_path, monkeypatch):
    (tmp_path / "mkdocs.yml").write_text("site_name: X\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["docs", "--out", str(tmp_path / "out")])
    assert result.exit_code == 0, result.output
    assert "epresso docs ." in result.output
    assert (tmp_path / "out" / "basics").is_dir()  # epresso's own docs


def test_build_empty_dir_hints(tmp_path):
    result = runner.invoke(app, ["build", str(tmp_path)])
    assert result.exit_code == 0
    assert "Built 0 pages" in result.output and "site.toml" in result.output
