"""Markdown link resolution — GitHub/wiki-style links to site URLs."""

from epresso.links import LinkResolver
from epresso.markdown import render_markdown


def _resolver():
    r = LinkResolver()
    r.add_name("configuration", "/docs/configuration/")
    r.add_name("routing", "/docs/routing/")
    r.add_name("layouts", "/docs/layouts/")
    r.add_name("Configuration", "/docs/configuration/")  # title (lowercased)
    # route paths (as the site's link_resolver registers them)
    r.add_name("/docs/configuration/", "/docs/configuration/")
    r.add_name("/docs/routing/", "/docs/routing/")
    r.add_name("/docs/layouts/", "/docs/layouts/")
    return r


def _cfg():
    return type("MC", (), {"highlight": True, "add_slug_ids": True, "autolink_headings": True})()


def test_resolve_relative_md_and_bare_names():
    r = _resolver()
    assert r.resolve("configuration.md") == "/docs/configuration/"
    assert r.resolve("Configuration") == "/docs/configuration/"
    assert r.resolve("layouts.md#route-object") == "/docs/layouts/#route-object"


def test_resolve_passes_through_absolute_external_anchor():
    r = _resolver()
    assert r.resolve("/docs/cli/") == "/docs/cli/"
    assert r.resolve("https://example.com") == "https://example.com"
    assert r.resolve("#anchor") == "#anchor"


def test_resolve_unresolvable_returns_none():
    r = _resolver()
    assert r.resolve("missing.md") is None
    assert r.resolve("Unknown Page") is None


def test_wiki_links_expand():
    cfg = _cfg()
    body = "See [[Configuration]] and [[Routing|the routing guide]]."
    out = render_markdown(body, cfg, link_resolver=_resolver()).html
    assert '<a href="/docs/configuration/">Configuration</a>' in out
    assert '<a href="/docs/routing/">the routing guide</a>' in out


def test_wiki_page_reference_expands():
    out = render_markdown("See [wiki_page:Layouts].", _cfg(), link_resolver=_resolver()).html
    assert '<a href="/docs/layouts/">Layouts</a>' in out


def test_resolve_absolute_md_link_to_page_url():
    r = _resolver()
    assert r.resolve("/docs/configuration.md") == "/docs/configuration/"
    assert r.resolve("/docs/routing.md#fragment") == "/docs/routing/#fragment"


def test_resolve_unresolvable_absolute_md_left_as_is():
    r = _resolver()
    assert r.resolve("/docs/does-not-exist.md") == "/docs/does-not-exist.md"


def test_resolve_absolute_non_md_passes_through():
    r = _resolver()
    assert r.resolve("/docs/configuration/") == "/docs/configuration/"
    assert r.resolve("/assets/logo.png") == "/assets/logo.png"


def test_absolute_md_link_rewritten_in_html():
    out = render_markdown(
        "See [Config](/docs/configuration.md).", _cfg(), link_resolver=_resolver()
    ).html
    assert '<a href="/docs/configuration/">Config</a>' in out


def test_relative_md_link_resolves():
    out = render_markdown("See [Config](configuration.md).", _cfg(), link_resolver=_resolver()).html
    assert '<a href="/docs/configuration/">Config</a>' in out


def test_unresolvable_wiki_link_left_as_is():
    out = render_markdown("See [[DoesNotExist]].", _cfg(), link_resolver=_resolver()).html
    assert "[[DoesNotExist]]" in out
    assert "<a" not in out
