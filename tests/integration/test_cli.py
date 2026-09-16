"""CLI tests via Typer's CliRunner (root passed explicitly via tmp_path)."""

from typer.testing import CliRunner

from epresso.cli import app
from epresso.fmt import format_text

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


def test_layers_command_reports_resolved_roots(tmp_path):
    r = tmp_path / "site"
    (r / "vendor" / "lib" / "components").mkdir(parents=True)
    (r / "site.toml").write_text('[layers]\nuse = ["path:./vendor/lib"]\n', encoding="utf-8")
    result = runner.invoke(app, ["layers", str(r)])
    assert result.exit_code == 0
    assert "vendor/lib" in result.output


def test_layers_command_without_layers(tmp_path):
    r = tmp_path / "site"
    (r).mkdir()
    result = runner.invoke(app, ["layers", str(r)])
    assert result.exit_code == 0
    assert "No layers" in result.output


def test_build_incremental_cached_second_run(tmp_path):
    r = tmp_path / "site"
    runner.invoke(app, ["init", str(r)])
    runner.invoke(app, ["build", str(r)])
    result = runner.invoke(app, ["build", str(r), "--no-clean"])
    assert result.exit_code == 0
    assert "1 cached" in result.output


def test_build_profile_writes_stats_file(tmp_path):
    r = tmp_path / "site"
    runner.invoke(app, ["init", str(r)])
    out = tmp_path / "prof.pstats"
    result = runner.invoke(app, ["build", str(r), "--profile", "--profile-out", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert "profile" in result.output.lower()
    assert "python -m pstats" in result.output


def test_profile_out_ignored_without_profile_flag(tmp_path):
    r = tmp_path / "site"
    runner.invoke(app, ["init", str(r)])
    out = tmp_path / "prof.pstats"
    result = runner.invoke(app, ["build", str(r), "--profile-out", str(out)])
    assert result.exit_code == 0
    assert not out.exists()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "epresso" in result.output.lower()


# -- `epresso new` (interactive + templates) --------------------------------


def test_new_non_interactive_requires_template(tmp_path, monkeypatch):
    from epresso import cli

    monkeypatch.setattr(cli, "_is_interactive", lambda: False)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["new"])
    assert result.exit_code == 1
    assert "no template given" in result.output.lower()


def test_new_yes_scaffolds_basic(tmp_path, monkeypatch):
    from epresso import cli

    monkeypatch.setattr(cli, "_is_interactive", lambda: False)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["new", "-y"])
    assert result.exit_code == 0
    assert (tmp_path / "site.toml").exists()
    assert (tmp_path / "pages" / "index.ep").exists()
    assert (tmp_path / "layouts" / "Base.ep").exists()


def test_new_basic_template(tmp_path):
    r = tmp_path / "site"
    result = runner.invoke(app, ["new", "basic", str(r)])
    assert result.exit_code == 0
    assert (r / "site.toml").exists()
    assert (r / "layouts" / "Base.ep").exists()
    assert (r / "content.config.py").exists()


def test_new_minimal_template(tmp_path):
    r = tmp_path / "site"
    result = runner.invoke(app, ["new", "minimal", str(r)])
    assert result.exit_code == 0
    assert (r / "site.toml").exists()
    assert (r / "pages" / "index.ep").exists()
    assert not (r / "layouts").exists()  # minimal ships no shell


def test_new_interactive_prompts_dir_and_template(tmp_path, monkeypatch):
    from epresso import cli

    monkeypatch.setattr(cli, "_is_interactive", lambda: True)
    monkeypatch.chdir(tmp_path)
    # dir -> "proj", then choose 4 (minimal)
    result = runner.invoke(app, ["new"], input="proj\n4\n")
    assert result.exit_code == 0
    assert (tmp_path / "proj" / "site.toml").exists()
    assert (tmp_path / "proj" / "pages" / "index.ep").exists()
    assert not (tmp_path / "proj" / "layouts").exists()


def test_new_interactive_defaults_to_basic_in_cwd(tmp_path, monkeypatch):
    from epresso import cli

    monkeypatch.setattr(cli, "_is_interactive", lambda: True)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["new"], input="\n\n")  # accept dir + template defaults
    assert result.exit_code == 0
    assert (tmp_path / "site.toml").exists()
    assert (tmp_path / "layouts" / "Base.ep").exists()


def test_new_interactive_reprompts_on_bad_choice(tmp_path, monkeypatch):
    from epresso import cli

    monkeypatch.setattr(cli, "_is_interactive", lambda: True)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["new"], input="site\n9\n3\n")  # 9 invalid, then docs(3)
    assert result.exit_code == 0
    assert (tmp_path / "site" / "site.toml").exists()


def test_fmt_stdin_matches_core_formatting():
    src = (
        "---\n"
        "from pydantic import BaseModel\n"
        "---\n"
        "\n"
        "<style>.a { color: red; }</style>\n"
        "<p>hello</p>\n"
        "<script>console.log(1);</script>\n"
    )
    result = runner.invoke(app, ["fmt", "--stdin"], input=src)
    assert result.exit_code == 0
    assert result.output == format_text(src)
    # canonical order: body -> script -> style
    assert result.output.index("<p>hello</p>") < result.output.index("<script>")
    assert result.output.index("<script>") < result.output.index("<style>")


def test_fmt_stdin_is_idempotent():
    once = runner.invoke(app, ["fmt", "--stdin"], input="<style>.a{color:red}</style>\n<p>hi</p>\n")
    assert once.exit_code == 0
    twice = runner.invoke(app, ["fmt", "--stdin"], input=once.output)
    assert twice.exit_code == 0
    assert twice.output == once.output


def test_fmt_stdin_rejects_check():
    result = runner.invoke(app, ["fmt", "--stdin", "--check"], input="<p>x</p>\n")
    assert result.exit_code == 2
