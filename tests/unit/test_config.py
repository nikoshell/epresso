from epresso.config import load_config
from epresso.errors import ConfigError


def test_defaults_when_no_file(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg.site.name == "My Site"
    assert cfg.build.trailing_slash == "always"
    assert cfg.dir_output() == tmp_path / "dist"


def test_load_site_toml(tmp_path):
    (tmp_path / "site.toml").write_text("[site]\nname = 'X'\nurl = 'https://x.io'\n")
    cfg = load_config(tmp_path)
    assert cfg.site.name == "X"
    assert cfg.site.url == "https://x.io"


def test_invalid_toml_raises(tmp_path):
    (tmp_path / "site.toml").write_text("not = [valid\n")
    try:
        load_config(tmp_path)
        raise AssertionError("expected ConfigError")
    except ConfigError:
        pass


def test_trailing_slash_config(tmp_path):
    (tmp_path / "site.toml").write_text("[build]\ntrailing_slash = 'never'\n")
    assert load_config(tmp_path).build.trailing_slash == "never"


def test_theme_config_is_opaque_passthrough(tmp_path):
    (tmp_path / "site.toml").write_text("[theme]\nsidebar = 'tree'\nnested = { color = 'red' }\n")
    cfg = load_config(tmp_path)
    assert cfg.theme["sidebar"] == "tree"
    assert cfg.theme["nested"]["color"] == "red"


def test_theme_config_defaults_to_empty(tmp_path):
    assert load_config(tmp_path).theme == {}
