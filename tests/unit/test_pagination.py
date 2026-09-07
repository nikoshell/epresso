"""Pagination helper tests."""

from epresso.routing import paginate


def _entries(n):
    return [{"id": i} for i in range(n)]


def test_single_page():
    routes = paginate(_entries(5), per_page=10, base_path="/blog/")
    assert len(routes) == 1
    r = routes[0]
    assert r.path == "/blog/"
    assert r.data["num_pages"] == 1
    assert r.data["prev"] is None and r.data["next"] is None


def test_multiple_pages():
    routes = paginate(_entries(25), per_page=10, base_path="/blog/")
    assert len(routes) == 3
    assert routes[0].path == "/blog/"
    assert routes[1].path == "/blog/page/2/"
    assert routes[2].path == "/blog/page/3/"
    assert routes[0].data["page"] == 1
    assert routes[2].data["prev"] == "/blog/page/2/"
    assert routes[2].data["next"] is None
    assert len(routes[2].data["entries"]) == 5


def test_paginate_works_in_get_static_paths(tmp_path):
    from epresso.site import Site

    root = tmp_path
    (root / "pages").mkdir()
    (root / "pages" / "blog" ).mkdir(parents=True)
    (root / "content" / "posts").mkdir(parents=True)
    (root / "content.config.py").write_text(
        "from epresso.content import define_collection\n"
        "posts = define_collection('posts', glob='*.md', base='./content/posts')\n"
    )
    for i in range(5):
        (root / "content" / "posts" / f"p{i}.md").write_text(f"---\ntitle: P{i}\n---\nbody\n")
    (root / "templates" / "layouts").mkdir(parents=True)
    (root / "templates" / "layouts" / "base.html").write_text(
        "<html><body>{% block content %}{% endblock %}</body></html>"
    )
    (root / "pages" / "blog" / "index.html").write_text(
        "{% extends 'layouts/base.html' %}{% block content %}{% for e in props.entries %}{{ e.id }};{% endfor %}{% endblock %}"
    )
    (root / "pages" / "blog" / "index.py").write_text(
        "from epresso.routing import paginate\n"
        "def get_static_paths():\n"
        "    return paginate(site.get_collection('posts'), per_page=2, base_path='/blog/', template='blog/index.html')\n"
    )
    site = Site.load(root)
    site.build()
    out = site.config.dir_output()
    assert (out / "blog" / "index.html").exists()
    assert (out / "blog" / "page" / "2" / "index.html").exists()
    assert (out / "blog" / "page" / "3" / "index.html").exists()
