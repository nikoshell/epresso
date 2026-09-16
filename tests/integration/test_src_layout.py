"""A project may keep all source under ``src/`` (Astro/Nuxt-style).

``public/``, ``dist/`` and ``site.toml`` / ``content.config.py`` stay at the root.
"""

from __future__ import annotations

from pathlib import Path

from epresso.site import Site

CONTENT_CONFIG = (
    "from pydantic import BaseModel\n"
    "from epresso.content import define_collection\n"
    "class Post(BaseModel):\n"
    "    title: str\n"
    "posts = define_collection('posts', glob='*.md', base='./content/posts', schema=Post)\n"
)

BASE = (
    "---\n---\n"
    "<!doctype html><html><head><title>{{ props.title }}</title></head>"
    "<body><slot /></body></html>\n"
)

FILES = {
    "site.toml": "[site]\nname = \"Src\"\nurl = \"https://example.com\"\n",
    "content.config.py": CONTENT_CONFIG,
    "src/content/posts/a.md": "---\ntitle: First\n---\n# First\n",
    "src/layouts/Base.ep": BASE,
    "src/components/Card.ep": '---\n---\n<p class="card">{{ content }}</p>\n',
    "src/pages/index.ep": '---\n---\n<Base title="Home"><Card>Hello from src</Card></Base>\n',
    "src/pages/blog.ep": (
        "---\n---\n<ul>{% for p in get_collection('posts') %}<li>{{ p.data.title }}</li>{% endfor %}</ul>\n"
    ),
    "public/robots.txt": "User-agent: *\n",
}


def _make(files: dict[str, str]) -> tuple[Path, Site]:
    import tempfile

    root = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root, Site.load(root)


def test_src_layout_builds():
    root, site = _make(FILES)
    result = site.build()

    assert site.config.source_root() == root / "src"
    assert result.pages  # not the silent 0-page success

    html = (site.config.dir_output() / "index.html").read_text()
    assert 'class="card"' in html and "Hello from src" in html
    assert "<title>Home</title>" in html

    # public/ stays at the project root and is copied verbatim
    assert (site.config.dir_output() / "robots.txt").read_text() == "User-agent: *\n"


def test_src_layout_collection_base_is_src_relative():
    _root, site = _make(FILES)
    site.build()
    html = (site.config.dir_output() / "blog" / "index.html").read_text()
    assert "<li>First</li>" in html


def test_without_src_the_layout_is_unchanged():
    files = {("pages/index.ep" if k == "src/pages/index.ep" else k.replace("src/", "")): v for k, v in FILES.items()}
    root, site = _make(files)
    site.build()
    assert site.config.source_root() == root
    assert "Hello from src" in (site.config.dir_output() / "index.html").read_text()
