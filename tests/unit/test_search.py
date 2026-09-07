"""Core BM-25 search index builder + scoring tests."""


from epresso import search


def test_tokenize():
    assert search.tokenize("Hello, World! 123") == ["hello", "world", "123"]
    assert search.tokenize("  Mixed   Case  ") == ["mixed", "case"]


def test_build_index_shape():
    units = [
        {"url": "/a/", "title": "Alpha", "section": "", "text": "the red apple"},
        {"url": "/b/", "title": "Beta", "section": "", "text": "the green apple"},
    ]
    idx = search.build_index(units)
    assert idx["version"] == 2
    assert "apple" in idx["index"]
    assert len(idx["index"]["apple"]) == 2  # in both units
    # postings are [unitIdx, precomputedScore], sorted by score descending
    assert idx["index"]["apple"][0] == [0, idx["index"]["apple"][0][1]]
    scores = [p[1] for p in idx["index"]["apple"]]
    assert scores == sorted(scores, reverse=True)
    assert units[0]["len"] > 0  # per-unit token length stored


def test_bm25_ranking_prefers_matching_unit():
    units = [
        {"url": "/apple/", "title": "Apples", "section": "", "text": "apple " * 12},
        {"url": "/mixed/", "title": "Mixed", "section": "", "text": "apple apple banana " * 3},
    ]
    idx = search.build_index(units)
    posts = idx["index"]["apple"]  # both units contain apple
    assert posts == sorted(posts, key=lambda p: p[1], reverse=True)  # sorted by score desc
    assert posts[0][0] == 0  # the apple-heavy unit ranks first


def test_split_sections_by_headings():
    html = (
        "<title>T</title><main><p>lead</p>"
        '<h2 id="one">One</h2><p>first body</p>'
        '<h2 id="two">Two</h2><p>second body</p></main>'
    )
    units = search.split_sections(html, "/page/")
    assert units[0]["anchor"] == ""
    assert units[1]["anchor"] == "one"
    assert units[2]["anchor"] == "two"
    assert "first body" in units[1]["text"]
    assert units[1]["section"] == "One"


def test_prefix_matching_finds_partial_terms():
    units = [{"url": "/md/", "title": "Markdown", "section": "", "text": "markdown is a lightweight format"}]
    idx = search.build_index(units)
    # A partial query term ("mark") matches index terms that start with it.
    keys = [t for t in idx["index"] if t.startswith("mark")]
    assert "markdown" in keys
    assert idx["index"]["markdown"]  # has postings
