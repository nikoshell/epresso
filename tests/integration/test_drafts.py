"""Drafts + scheduled-content exclusion tests."""

import datetime

from epresso.site import Site


def _make(posts):
    import tempfile
    from pathlib import Path

    d = tempfile.mkdtemp()
    root = Path(d)
    (root / "content" / "posts").mkdir(parents=True)
    (root / "pages" / "posts").mkdir(parents=True)
    (root / "content.config.py").write_text(
        "from pydantic import BaseModel\n"
        "from epresso.content import define_collection\n"
        "class Post(BaseModel):\n"
        "    title: str\n"
        "    date: str = ''\n"
        "    draft: bool = False\n"
        "posts = define_collection('posts', glob='*.md', base='./content/posts', schema=Post)\n"
    )
    (root / "pages" / "posts" / "[slug].html").write_text(
        "{% extends 'layouts/base.html' %}{% block content %}{{ props.title }}{% endblock %}"
    )
    (root / "pages" / "posts" / "[slug].py").write_text(
        "from epresso.routing import Route\n"
        "def get_static_paths():\n"
        "    return [Route(path=f'/posts/{p.id}/', params={'slug': p.id}, data=p) for p in site.get_collection('posts')]\n"
    )
    (root / "templates" / "layouts").mkdir(parents=True)
    (root / "templates" / "layouts" / "base.html").write_text("<html><body>{% block content %}{% endblock %}</body></html>")
    for name, fm in posts.items():
        (root / "content" / "posts" / f"{name}.md").write_text(f"---\n{fm}\n---\nbody\n")
    return root, Site.load(root)


def test_draft_and_scheduled_excluded_in_production():
    future = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
    root, site = _make(
        {
            "live": "title: Live\ndate: 2020-01-01",
            "drafty": "title: Drafty\nk: 1\ndraft: true",
            "upcoming": f"title: Upcoming\ndate: {future}",
        }
    )
    site.build()
    out = site.config.dir_output()
    # only 'live' should produce a route in production
    assert (out / "posts" / "live" / "index.html").exists()
    assert not (out / "posts" / "drafty" / "index.html").exists()
    assert not (out / "posts" / "upcoming" / "index.html").exists()


def test_drafts_visible_outside_production():
    root, site = _make({"live": "title: Live", "drafty": "title: Drafty\ndraft: true"})
    # dev mode (no build → not production) shows all
    ids = [e.id for e in site.get_collection("posts")]
    assert "drafty" in ids
