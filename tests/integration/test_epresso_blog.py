"""epresso_blog: MkDocs blog posts → MkDocs URLs, listings, RSS, docs sidebar."""

import re

from typer.testing import CliRunner

from epresso.cli import app

runner = CliRunner()


def _post(day: str, title: str, cats: list[str], extra: str = "") -> str:
    c = "".join(f"\n  - {x}" for x in cats)
    return f"---\ndate: {day}\nauthors: [jo]\ncategories:{c}\n{extra}---\n\n# {title}\n\nIntro text.\n\n<!-- more -->\n\nRest.\n"


def _site(tmp_path, n_posts: int = 12):
    d = tmp_path / "proj"
    posts = d / "docs" / "blog" / "posts"
    (posts / "img").mkdir(parents=True)
    (posts / "img" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (d / "docs" / "index.md").write_text("# Home\n\nhi\n", encoding="utf-8")
    (d / "docs" / "guide.md").write_text("# Guide\n\ng\n", encoding="utf-8")
    (d / "docs" / "blog" / "index.md").write_text("# Blog\n\nOur news.\n", encoding="utf-8")
    (d / "docs" / "blog" / ".authors.yml").write_text("authors:\n  jo:\n    name: Jo Doe\n", encoding="utf-8")
    for i in range(n_posts):
        (posts / f"p{i}.md").write_text(_post(f"202{i % 3}-0{1 + i % 9}-1{i % 9}", f"Post `{i}` is here!", ["News" if i % 2 else "Big Release"]), encoding="utf-8")
    (posts / "custom.md").write_text(_post("2020-05-01", "Custom", [], "slug: my-slug\n") + "\n![a](img/a.png)\n", encoding="utf-8")
    (posts / "wip.md").write_text(_post("2022-01-01", "Draft one", [], "draft: true\n"), encoding="utf-8")
    (d / "mkdocs.yml").write_text(
        "site_name: X\nsite_url: https://x.dev/\nnav:\n  - index.md\n  - guide.md\n  - Blog:\n    - blog/index.md\nplugins:\n  - blog:\n      pagination_per_page: 5\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    result = runner.invoke(app, ["docs", str(d), "--out", str(out)])
    assert result.exit_code == 0, result.output
    return out


def test_blog_urls_listings_and_sidebar(tmp_path):
    out = _site(tmp_path)
    post = out / "blog" / "2020" / "01" / "10" / "post-0-is-here" / "index.html"
    assert post.is_file()  # title slug, MkDocs date format
    html = post.read_text(encoding="utf-8")
    assert "Jo Doe" in html and "Post 0 is here!" in html and "Rest." in html
    assert (out / "blog" / "2020" / "05" / "01" / "my-slug" / "index.html").is_file()  # slug: wins
    assert not any("draft-one" in str(p) for p in out.rglob("index.html"))  # drafts hidden
    assert (out / "blog" / "page" / "2" / "index.html").is_file() and (out / "blog" / "page" / "3" / "index.html").is_file()
    assert (out / "blog" / "archive" / "2021" / "index.html").is_file()
    assert (out / "blog" / "category" / "big-release" / "index.html").is_file()
    index = (out / "blog" / "index.html").read_text(encoding="utf-8")
    assert "Our news." in index and "Intro text." in index and "Rest." not in index  # excerpt
    assert not (out / "blog" / "posts" / "p0" / "index.html").exists()  # not also a docs page
    custom = (out / "blog" / "2020" / "05" / "01" / "my-slug" / "index.html").read_text(encoding="utf-8")
    assert "/blog/posts/img/a.png" in custom and (out / "blog" / "posts" / "img" / "a.png").is_file()
    assert not list(out.glob("_docs-assets/*/blog")), "blog images published twice"
    nav = index[index.index('id="sidebar-nav"') :]
    assert re.search(r"Guide.*Blog.*All posts", nav, re.S)
    rss = (out / "blog" / "rss.xml").read_text(encoding="utf-8")
    assert "my-slug" in rss and "<item>" in rss


def test_import_maps_blog_options(tmp_path):
    from epresso.mkdocs_import import mkdocs_to_docs_config

    (tmp_path / "mkdocs.yml").write_text(
        "site_name: X\nplugins:\n  - blog:\n      pagination_per_page: 5\n      post_slugify: !!python/name:pymdownx.slugs.uslugify\n",
        encoding="utf-8",
    )
    cfg, warn = mkdocs_to_docs_config(tmp_path / "mkdocs.yml")
    assert cfg["blog"] == {"pagination_per_page": 5}
    assert not any("blog" in w for w in warn)
