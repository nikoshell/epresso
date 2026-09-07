"""Incremental build tests — data edits re-render only affected paths."""



def test_first_build_renders_all(site):
    result = site.build()
    assert result.skipped == 0
    assert len(result.pages) == 4  # /, /blog/, /blog/a/, /blog/b/


def test_second_build_without_changes_is_all_cached(site):
    site.build()
    result = site.build(clean=False)
    assert result.skipped == len(result.pages)
    assert len(result.pages) == 4


def test_edit_content_rerenders_only_affected_path(site, tmp_path):
    site.build()

    # change post 'a' only
    a = tmp_path / "content" / "posts" / "a.md"
    a.write_text(a.read_text().replace("Body **bold**", "Body **bold v2**"))
    result = site.build(clean=False)

    # 4 pages: '/' and '/blog/b/' cached (data unchanged); '/blog/a/' and
    # '/blog/index.html' re-rendered (post changed; index lists posts).
    assert result.skipped == 2
    assert len(result.pages) == 4
    out = site.config.dir_output()
    assert "Body <strong>bold v2</strong>" in (out / "blog" / "a" / "index.html").read_text()
    # untouched page still served from cache
    assert "Bee" in (out / "blog" / "b" / "index.html").read_text()


def test_template_change_invalidates_all(site, tmp_path):
    site.build()
    tmpl = tmp_path / "templates" / "layouts" / "base.html"
    tmpl.write_text(tmpl.read_text().replace("epresso", "EPRESSO"))
    result = site.build(clean=False)
    assert result.skipped == 0  # code change → full rebuild


def test_new_entry_adds_route(site, tmp_path):
    site.build()
    (tmp_path / "content" / "posts" / "c.md").write_text("---\ntitle: C\n---\n# Cee\n")
    result = site.build(clean=False)
    # c is new (rendered), a/b/index cached, blog index re-rendered (list changed)
    assert len(result.pages) == 5
    assert (site.config.dir_output() / "blog" / "c" / "index.html").exists()


def test_removed_entry_prunes_cached_output(site, tmp_path):
    site.build()
    (tmp_path / "content" / "posts" / "b.md").unlink()
    site.build(clean=False)
    cache_dir = site.config.cache_dir()
    assert not (cache_dir / "output" / "blog" / "b" / "index.html").exists()


def test_cache_manifest_written(site):
    site.build()
    mf = site.config.cache_dir() / "incremental.json"
    assert mf.exists()
    import json

    data = json.loads(mf.read_text())
    assert data["version"] == 1
    assert "/blog/a/" in data["paths"]
