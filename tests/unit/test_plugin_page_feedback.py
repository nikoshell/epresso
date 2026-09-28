"""The Umami-backed page-feedback widget: injected only on gated doc pages.

Gated on ``UMAMI_WEBSITE_ID`` (analytics configured) plus ``PAGE_FEEDBACK`` not
being off, and scoped to routes that carry a page slug. The widget markup is
hidden until the injected script reveals it.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from epresso.site import Site

PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "epresso_page_feedback.py"
THEME = Path(__file__).resolve().parents[2] / "themes" / "docs"
WEBSITE_ID = "69485d2d-7605-40f6-9252-634f3dcc0209"

DOC_HTML = (
    "<!doctype html><html><head><title>x</title></head>"
    '<body><article class="doc"><p>hi</p></article></body></html>'
)
DOC_CTX = {"path": "/a/", "params": {"slug": "a"}}


def _load():
    spec = importlib.util.spec_from_file_location("_epresso_page_feedback", PLUGIN)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _on(monkeypatch):
    monkeypatch.setenv("UMAMI_WEBSITE_ID", WEBSITE_ID)
    monkeypatch.delenv("PAGE_FEEDBACK", raising=False)
    return _load()


def test_injects_widget_and_tracker_when_enabled(monkeypatch):
    out = _on(monkeypatch)._inject(DOC_HTML, DOC_CTX)
    assert "data-page-feedback" in out
    assert "Was this page helpful?" in out
    assert 'data-feedback="yes"' in out and 'data-feedback="no"' in out
    assert "umami.track(EVENT, { helpful: helpful, page: location.pathname })" in out
    # Before the closing </article>, and only once.
    assert out.index("data-page-feedback") < out.index("</article>")
    assert out.count('class="page-feedback"') == 1


def test_noop_without_analytics(monkeypatch):
    monkeypatch.delenv("UMAMI_WEBSITE_ID", raising=False)
    monkeypatch.delenv("PAGE_FEEDBACK", raising=False)
    assert _load()._inject(DOC_HTML, DOC_CTX) == DOC_HTML


def test_noop_when_page_has_no_slug(monkeypatch):
    mod = _on(monkeypatch)
    assert mod._inject(DOC_HTML, {"path": "/", "params": {}}) == DOC_HTML


def test_disable_switch_keeps_analytics_but_drops_widget(monkeypatch):
    monkeypatch.setenv("UMAMI_WEBSITE_ID", WEBSITE_ID)
    monkeypatch.setenv("PAGE_FEEDBACK", "off")
    assert _load()._inject(DOC_HTML, DOC_CTX) == DOC_HTML


def test_transform_is_idempotent(monkeypatch):
    mod = _on(monkeypatch)
    once = mod._inject(DOC_HTML, DOC_CTX)
    assert mod._inject(once, DOC_CTX) == once


def test_docs_theme_doc_page_gets_it_and_landing_does_not(monkeypatch):
    _on(monkeypatch)
    site = Site.load(THEME)
    page, _ = site.render_at("/guides/build/commands/")
    assert "data-page-feedback" in page
    landing, _ = site.render_at("/")
    assert "data-page-feedback" not in landing
