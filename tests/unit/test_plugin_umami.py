"""The bundled Umami analytics plugin.

The snippet is injected only when ``UMAMI_WEBSITE_ID`` is set, so the plugin can
be listed in a site's ``[plugins]`` and still no-op for local dev / preview.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from epresso.site import Site

PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "epresso_umami.py"
WEBSITE_ID = "69485d2d-7605-40f6-9252-634f3dcc0209"


def _load():
    spec = importlib.util.spec_from_file_location("_epresso_umami", PLUGIN)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build(tmp_path, monkeypatch, website_id: str | None):
    if website_id is None:
        monkeypatch.delenv("UMAMI_WEBSITE_ID", raising=False)
    else:
        monkeypatch.setenv("UMAMI_WEBSITE_ID", website_id)
    (tmp_path / "pages").mkdir()
    (tmp_path / "pages" / "index.ep").write_text(
        "---\n---\n<!doctype html><html lang='en'><head><title>hi</title></head><body><p>hi</p></body></html>",
        encoding="utf-8",
    )
    site = Site.load(tmp_path)
    site.plugins.register(_load().umami)
    site.build()
    return (site.config.dir_output() / "index.html").read_text(encoding="utf-8")


def test_injects_snippet_into_head_when_configured(tmp_path, monkeypatch):
    html = _build(tmp_path, monkeypatch, WEBSITE_ID)
    assert '<script defer src="https://cloud.umami.is/script.js"' in html
    assert f'data-website-id="{WEBSITE_ID}"' in html
    assert html.count("data-website-id=") == 1
    assert html.index("data-website-id=") < html.index("</head>")


def test_is_a_noop_without_a_website_id(tmp_path, monkeypatch):
    assert "umami" not in _build(tmp_path, monkeypatch, None).lower()


def test_self_hosted_script_url(tmp_path, monkeypatch):
    monkeypatch.setenv("UMAMI_SCRIPT_URL", "https://umami.example.com/script.js")
    html = _build(tmp_path, monkeypatch, WEBSITE_ID)
    assert 'src="https://umami.example.com/script.js"' in html
