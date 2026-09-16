"""Shared pytest fixtures and a helper to build throwaway epresso projects."""

from __future__ import annotations

from pathlib import Path

import pytest

from epresso.site import Site


def make_site(tmp_path: Path, files: dict[str, str]) -> Site:
    """Write ``files`` (relative path → content) under tmp_path and load a Site."""
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return Site.load(tmp_path)


@pytest.fixture
def site(tmp_path):
    files = {
        "site.toml": (
            "[site]\nname = \"Test\"\nurl = \"https://example.com\"\n\n"
            "[build]\ntrailing_slash = \"always\"\n"
        ),
        "content.config.py": (
            "from pydantic import BaseModel\n"
            "from epresso.content import define_collection\n"
            "class Post(BaseModel):\n    title: str\n    date: str = ''\n    tags: list[str] = []\n"
            "posts = define_collection('posts', glob='*.md', base='./content/posts', schema=Post)\n"
        ),
        "content/posts/a.md": (
            "---\ntitle: A\n---\n# Hello\n\nBody **bold**.\n"
        ),
        "content/posts/b.md": (
            "---\ntitle: B\ndate: 2026-01-01\ntags: [x, y]\n---\n# Bee\n"
        ),
        "layouts/Base.ep": (
            "---\n"
            "from pydantic import BaseModel\n"
            "class Props(BaseModel):\n"
            "    title: str = 'epresso'\n"
            "---\n"
            "<!doctype html><html><head><title>{{ props.title }}</title></head>"
            "<body>{{ content }}</body></html>\n"
        ),
        "pages/index.md": (
            "---\ntitle: Home\nlayout: Base\n---\n# Welcome\n"
        ),
        "pages/blog/index.ep": (
            "---\n---\n"
            '<Base title="Blog"><ul>{% for p in get_collection(\'posts\') %}'
            "<li>{{ p.data.title }}</li>{% endfor %}</ul></Base>\n"
        ),
        "pages/blog/[slug].ep": (
            "---\n"
            "def get_static_paths():\n"
            "    return [dict(params={'slug': p.id}, data=p) for p in site.get_collection('posts')]\n"
            "---\n"
            "<Base title={props.title}><h1>{{ props.title }}</h1>{{ content }}</Base>\n"
        ),
        "pages/data.json.py": (
            "import json\n"
            "def get():\n"
            "    return 'application/json', json.dumps([p.data.title for p in site.get_collection('posts')])\n"
        ),
    }
    return make_site(tmp_path, files)
