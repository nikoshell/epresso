"""Core BM-25 search index builder + scoring tests."""


from epresso import search


def test_tokenize():
    assert search.tokenize("Hello, World! 123") == ["hello", "world", "123"]
    assert search.tokenize("  Mixed   Case  ") == ["mixed", "case"]


def test_entities_decoded_not_left_for_client_to_double_escape():
    html = "<title>T</title><body><main><p>Content &amp; data &lt;x&gt;</p></main></body>"
    assert search.split_sections(html, "/x/")[0]["text"] == "Content & data <x>"


def test_breadcrumb_excludes_current_page_and_joins_with_slash():
    html = (
        "<html><head><title>Markdown \u00b7 epresso</title></head><body><main>"
        '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a>'
        '<span class="crumb-sep">/</span><span>Guides</span>'
        '<span class="crumb-sep">/</span><span>Content &amp; data</span>'
        '<span class="crumb-sep">/</span><span class="crumb-cur">Markdown</span></nav>'
        "<h1>Markdown</h1><p>markdown is a lightweight format</p></main></body></html>"
    )
    unit = search.split_sections(html, "/guides/content/markdown/")[0]
    assert unit["crumb"] == "Home / Guides / Content & data"
    assert "Markdown" not in unit["crumb"]  # current page: already the title
    # crumb is display-only metadata, never in the searchable/scoring text
    assert "Home" not in unit["text"] and "Guides" not in unit["text"]


def test_root_page_has_no_breadcrumb():
    html = "<html><head><title>epresso</title></head><body><main><h1>epresso</h1><p>intro</p></main></body></html>"
    assert search.split_sections(html, "/")[0]["crumb"] == ""


def test_pager_nav_excluded_so_it_does_not_leak_neighbour_titles():
    html = (
        "<html><head><title>Layouts \u00b7 epresso</title></head><body><main>"
        "<h1>Layouts</h1><h2 id=\"a\">A</h2><p>layouts explain how pages compose.</p>"
        '<nav class="pager" aria-label="Docs pagination">'
        '<a class="pager-link" href="/basics/pages/"><span class="pager-label">Previous</span>'
        '<span class="pager-title">Pages</span></a>'
        '<a class="pager-link pager-next" href="/basics/project-structure/">'
        '<span class="pager-label">Next</span><span class="pager-title">Project structure</span></a>'
        "</nav></main></body></html>"
    )
    units = search.split_sections(html, "/basics/layouts/")
    assert not any("Project structure" in u["text"] or "Pages" in u["text"] for u in units)


def test_lead_unit_drops_breadcrumbs_and_duplicate_h1():
    html = (
        "<html><head><title>Project structure \u00b7 epresso</title></head><body><main>"
        '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a>'
        '<span class="crumb-sep">/</span><span class="crumb-cur">Project structure</span></nav>'
        '<h1 data-epresso-ab12>Project structure</h1>'
        "<pre>tree\ncontent/  # collections\nstructure/  # page regions</pre>"
        "</main></body></html>"
    )
    unit = search.split_sections(html, "/basics/project-structure/")[0]
    assert unit["title"] == "Project structure"
    assert "Home" not in unit["text"]
    assert "Project structure" not in unit["text"]
    assert "structure/" in unit["text"]


def test_title_prefers_h1_over_document_title():
    """<title> carries the theme's site-name suffix; the <h1> is the authored one."""
    html = (
        "<html><head><title>Pages \u00b7 epresso</title></head><body><main>"
        '<h1 data-epresso-ab12>Pages<a class="heading-anchor" href="#pages">#</a></h1>'
        "<p>" + "a page is any file under pages " * 8 + "</p></main></body></html>"
    )
    assert search.split_sections(html, "/pages/")[0]["title"] == "Pages"
    # no <h1> in main -> document title
    html = "<html><head><title>T</title></head><body><main><p>lead</p></main></body></html>"
    assert search.split_sections(html, "/x/")[0]["title"] == "T"
    # no <title> either -> empty, and the result renderer falls back to the section
    assert search.split_sections("<main><p>lead</p></main>", "/x/")[0]["title"] == ""


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


def test_page_title_tolerates_attributes():
    """The scoper stamps data-epresso-* onto every element, <title> included."""
    assert search.page_title('<html><head><title data-epresso-ab12>Markdown · epresso</title>') == "Markdown · epresso"
    assert search.page_title('<title>Plain</title>') == "Plain"
    assert search.page_title("<html><body>no title</body></html>") == ""


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
