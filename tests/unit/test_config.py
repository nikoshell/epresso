from epresso.config import load_config
from epresso.errors import ConfigError


def test_defaults_when_no_file(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg.site.name == "My Site"
    assert cfg.build.trailing_slash == "always"
    assert cfg.dir_output() == tmp_path / "dist"


def test_markdown_backend_defaults_to_native(tmp_path):
    assert load_config(tmp_path).markdown.backend == "native"


def test_markdown_backend_rejects_unknown_value(tmp_path):
    (tmp_path / "site.toml").write_text("[markdown]\nbackend = 'quickjs'\n")
    try:
        load_config(tmp_path)
        raise AssertionError("expected ConfigError for an unknown backend")
    except ConfigError:
        pass


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


def test_source_dirs_are_resolved_against_the_project_root(tmp_path):
    """There is no `src/` layout: a top-level `src/` is an ordinary directory and
    never relocates pages, components, layouts, content, styles or assets."""
    (tmp_path / "src").mkdir()
    cfg = load_config(tmp_path)
    assert cfg.dir_pages() == tmp_path / "pages"
    assert cfg.dir_layouts() == tmp_path / "layouts"
    assert cfg.dir_components() == tmp_path / "components"
    assert cfg.dir_content() == tmp_path / "content"
    assert cfg.dir_styles() == tmp_path / "styles"
    assert cfg.dir_assets() == tmp_path / "assets"
    assert cfg.dir_static() == tmp_path / "public"
    assert cfg.dir_output() == tmp_path / "dist"
    # project root stays put: public/, dist/, .cache/ and config files
    assert cfg.dir_static() == tmp_path / "public"
    assert cfg.dir_output() == tmp_path / "dist"
    assert cfg.cache_dir() == tmp_path / ".cache"
