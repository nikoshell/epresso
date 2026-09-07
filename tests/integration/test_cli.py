"""CLI tests via Typer's CliRunner (root passed explicitly via tmp_path)."""

from typer.testing import CliRunner

from epresso.cli import app

runner = CliRunner()


def test_init_scaffolds_project(tmp_path):
    r = tmp_path / "site"
    result = runner.invoke(app, ["init", str(r)])
    assert result.exit_code == 0
    for f in ["site.toml", "pages/index.ep", "layouts/Base.ep", "content.config.py", "components", "styles", "public"]:
        assert (r / f).exists(), f"missing {f}"


def test_init_then_build(tmp_path):
    r = tmp_path / "site"
    runner.invoke(app, ["init", str(r)])
    result = runner.invoke(app, ["build", str(r)])
    assert result.exit_code == 0
    assert (r / "dist" / "index.html").exists()
    assert "pages" in result.output.lower()


def test_docs_command_defaults_to_port_4321():
    result = runner.invoke(app, ["docs", "--help"])
    assert result.exit_code == 0
    assert "4321" in result.output


def test_docs_missing_root_errors(tmp_path):
    result = runner.invoke(app, ["docs", str(tmp_path / "nope")])
    assert result.exit_code == 1
    assert "no docs project" in result.output.lower()


def test_check_reports_routes(tmp_path):
    r = tmp_path / "site"
    runner.invoke(app, ["init", str(r)])
    result = runner.invoke(app, ["check", str(r)])
    assert result.exit_code == 0
    assert "Routes: 1" in result.output


def test_build_incremental_cached_second_run(tmp_path):
    r = tmp_path / "site"
    runner.invoke(app, ["init", str(r)])
    runner.invoke(app, ["build", str(r)])
    result = runner.invoke(app, ["build", str(r), "--no-clean"])
    assert result.exit_code == 0
    assert "1 cached" in result.output


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "epresso" in result.output.lower()
