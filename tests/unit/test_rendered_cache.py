"""Unit tests for the RenderedBodyCache (persisted content bodies)."""

from epresso.incremental import RenderedBodyCache


def test_load_returns_empty_when_missing(tmp_path):
    cache = RenderedBodyCache(tmp_path)
    assert cache.load("cfg", "code") == {}


def test_store_then_load_roundtrip(tmp_path):
    cache = RenderedBodyCache(tmp_path)
    cache.store("cfg1", "code1", {"d1": {"html": "<p>hi</p>", "metadata": {"headings": []}}})
    got = cache.load("cfg1", "code1")
    assert got == {"d1": {"html": "<p>hi</p>", "metadata": {"headings": []}}}


def test_invalidated_when_config_changes(tmp_path):
    cache = RenderedBodyCache(tmp_path)
    cache.store("cfg1", "code1", {"d1": {"html": "<p>hi</p>", "metadata": {}}})
    assert cache.load("cfg2", "code1") == {}  # config changed -> stale


def test_invalidated_when_code_changes(tmp_path):
    cache = RenderedBodyCache(tmp_path)
    cache.store("cfg1", "code1", {"d1": {"html": "<p>hi</p>", "metadata": {}}})
    assert cache.load("cfg1", "code2") == {}  # code changed -> stale


def test_clear_preserves_rendered_cache(tmp_path):
    from epresso.incremental import IncrementalCache

    rc = RenderedBodyCache(tmp_path)
    rc.store("cfg", "code", {"d1": {"html": "<p>hi</p>", "metadata": {}}})
    inc = IncrementalCache(tmp_path)
    inc.clear()  # must not wipe rendered.json
    assert rc.load("cfg", "code") == {"d1": {"html": "<p>hi</p>", "metadata": {}}}
