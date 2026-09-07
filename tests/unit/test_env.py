"""Environment support tests: site.<env>.toml layering + .env.<env> loading."""

import os
from pathlib import Path

from epresso.config import _deep_merge, load_config, load_env_file
from epresso.site import Site


def _make(files, tmp_path):
    root = Path(tmp_path)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


def test_load_config_no_env(tmp_path):
    root = _make({"site.toml": '[site]\nname = "Base"\nurl = "https://x.com"\n'}, tmp_path)
    cfg = load_config(root)
    assert cfg.site.name == "Base"
    assert cfg.env is None


def test_load_config_env_layering(tmp_path):
    root = _make(
        {
            "site.toml": '[site]\nname = "Base"\nurl = "https://x.com"\n[build]\ntrailing_slash = "always"\ncompress_html = false\n',
            "site.preview.toml": '[site]\nurl = "https://preview.x.com"\n[build]\ncompress_html = true\n',
        },
        tmp_path,
    )
    cfg = load_config(root, env="preview")
    assert cfg.site.name == "Base"  # inherited
    assert cfg.site.url == "https://preview.x.com"  # overridden
    assert cfg.build.compress_html is True  # deep-merged
    assert cfg.env == "preview"


def test_load_env_file(tmp_path):
    root = _make({".env.development": 'EP_SESSIONS_API="https://a"\nEP_FAST_BUILD=true\n# comment\n'}, tmp_path)
    v = load_env_file(root, "development")
    assert v["EP_SESSIONS_API"] == "https://a"
    assert v["EP_FAST_BUILD"] == "true"  # value kept as string, quotes stripped
    assert load_env_file(root, None) == {}
    assert load_env_file(root, "nope") == {}


def test_site_load_exposes_env_and_vars(tmp_path):
    files = {
        "site.toml": '[site]\nname = "T"\nurl = "https://x.com"\n',
        "site.production.toml": '[site]\nurl = "https://prod.x.com"\n',
        ".env.production": 'EP_SESSIONS_API="https://prod/api/sessions.json"\n',
        "pages/index.html": '<span data-env="{{ env }}">{{ env_vars.EP_SESSIONS_API }}</span>',
    }
    root = _make(files, tmp_path)
    site = Site.load(root, env="production")
    assert site.env_name == "production"
    assert site.config.site.url == "https://prod.x.com"
    assert site.env_vars["EP_SESSIONS_API"] == "https://prod/api/sessions.json"
    site.build()
    html = (root / "dist" / "index.html").read_text()
    assert 'data-env="production"' in html
    assert "https://prod/api/sessions.json" in html


def test_epresso_env_envvar_default(tmp_path, monkeypatch):
    files = {"site.toml": '[site]\nname = "T"\nurl = "https://x.com"\n',
             ".env.staging": 'EP_SESSIONS_API="https://stage/api"\n'}
    root = _make(files, tmp_path)
    monkeypatch.setenv("EPRESSO_ENV", "staging")
    site = Site.load(root)  # no explicit env -> EPRESSO_ENV
    assert site.env_name == "staging"
    assert site.env_vars["EP_SESSIONS_API"] == "https://stage/api"


def test_env_vars_injected_to_os_environ(tmp_path, monkeypatch):
    files = {"site.toml": '[site]\nname = "T"\n',
             ".env.production": 'EP_OPENSPACES_UNIQUE="https://prod/ical"\n'}
    root = _make(files, tmp_path)
    monkeypatch.setenv("EPRESSO_ENV", "production")
    Site.load(root)
    assert os.environ.get("EP_OPENSPACES_UNIQUE") == "https://prod/ical"


def test_deep_merge():
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    over = {"a": {"y": 20, "z": 30}, "c": 4}
    out = _deep_merge(base, over)
    assert out == {"a": {"x": 1, "y": 20, "z": 30}, "b": 3, "c": 4}
