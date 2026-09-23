"""`Site.load(load=False)` defers the content load to `build`.

A CLI build used to load every collection and render every Markdown body twice —
once in `Site.load`, once in `build`.
"""

from pathlib import Path

import epresso.site as site_mod
from epresso.site import Site


def _write(root: Path) -> None:
    (root / "pages").mkdir(parents=True)
    (root / "pages" / "index.ep").write_text("---\n---\n<p>hi</p>\n", encoding="utf-8")


def test_load_false_defers_and_build_loads_once(tmp_path, monkeypatch):
    _write(tmp_path)
    calls = {"n": 0}
    original = site_mod.load_collections

    def counting(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(site_mod, "load_collections", counting)

    site = Site.load(tmp_path, load=False)
    assert calls["n"] == 0  # nothing loaded until build
    assert site._loaded is False

    result = site.build()
    assert calls["n"] == 1  # loaded exactly once
    assert "/" in result.pages


def test_default_load_still_loads(tmp_path):
    _write(tmp_path)
    assert Site.load(tmp_path)._loaded is True


def test_resolve_routes_is_cached_until_a_reload(site):
    """The dev server asks several times per request; expansion is expensive."""
    routes = site.resolve_routes()
    assert site.resolve_routes() is routes  # cached for the life of a load
    site._do_load()
    assert site._routes is None  # a load invalidates it
    assert site.resolve_routes() is not routes  # (mid-render expansion is dropped too)


def test_rendered_bodies_are_reused_across_loads(site, monkeypatch):
    """A reload re-renders only what changed — the dev edit-to-reload path."""
    import epresso.site as site_mod

    calls = {"n": 0}
    original = site_mod.render_markdown

    def counting(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(site_mod, "render_markdown", counting)

    site._do_load()
    assert calls["n"] == 0  # unchanged entries come from the persisted cache

    edited = site.config.root / "content" / "posts" / "a.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
    site._do_load()
    assert calls["n"] == 1  # only the edited entry re-renders
