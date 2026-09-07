"""Configurable draft/private visibility per environment.

Covers: default behaviour (drafts/private shown in dev, hidden in production)
and ``[content] show_drafts`` / ``show_private`` overrides via site.toml and
per-environment ``site.<env>.toml`` files.
"""

from __future__ import annotations

from pathlib import Path

from epresso.site import Site

CONFIG = (
    "[site]\nname = \"Test\"\nurl = \"https://example.com\"\n\n"
    "[build]\ntrailing_slash = \"always\"\n"
)
COLLECTION = (
    "from pydantic import BaseModel\n"
    "from epresso.content import define_collection\n"
    "class Post(BaseModel):\n"
    "    title: str\n"
    "    draft: bool = False\n"
    "    private: bool = False\n"
    "posts = define_collection('posts', glob='*.md', base='./content/posts', schema=Post)\n"
)
POSTS = {
    "content/posts/pub.md": "---\ntitle: Pub\n---\n# Public\n",
    "content/posts/draft.md": "---\ntitle: Draft\ndraft: true\n---\n# Draft\n",
    "content/posts/priv.md": "---\ntitle: Priv\nprivate: true\n---\n# Private\n",
}


def _site(tmp_path: Path, files: dict[str, str], env: str | None = None) -> Site:
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return Site.load(tmp_path, env=env)


def _ids(site: Site) -> set[str]:
    return {e.id for e in site.get_collection("posts")}


def _base(tmp_path: Path) -> dict[str, str]:
    return {
        "site.toml": CONFIG,
        "content.config.py": COLLECTION,
        **POSTS,
    }


def test_default_hides_draft_and_private_in_production(tmp_path: Path) -> None:
    site = _site(tmp_path, _base(tmp_path))
    site._production = True  # emulate a production build
    ids = _ids(site)
    assert "pub" in ids
    assert "draft" not in ids
    assert "priv" not in ids


def test_default_shows_draft_and_private_in_development(tmp_path: Path) -> None:
    site = _site(tmp_path, _base(tmp_path))
    site._production = False  # emulate a dev build
    ids = _ids(site)
    assert {"pub", "draft", "priv"} <= ids


def test_site_toml_false_hides_everywhere_without_env_override(tmp_path: Path) -> None:
    base = _base(tmp_path)
    base["site.toml"] = CONFIG + "[content]\nshow_drafts = false\nshow_private = false\n"
    site = _site(tmp_path, base)
    site._production = False
    ids = _ids(site)
    assert "pub" in ids
    assert "draft" not in ids
    assert "priv" not in ids


def test_env_file_restores_dev_visibility(tmp_path: Path) -> None:
    """site.development.toml flips drafts/private back on for `epresso dev`."""
    files = _base(tmp_path)
    files["site.toml"] = CONFIG + "[content]\nshow_drafts = false\nshow_private = false\n"
    files["site.development.toml"] = "[content]\nshow_drafts = true\nshow_private = true\n"
    site = _site(tmp_path, files, env="development")
    site._production = False
    assert {"pub", "draft", "priv"} <= _ids(site)


def test_production_override_shows_for_staging_review(tmp_path: Path) -> None:
    files = _base(tmp_path)
    files["site.production.toml"] = "[content]\nshow_drafts = true\nshow_private = true\n"
    site = _site(tmp_path, files, env="production")
    site._production = True
    assert {"pub", "draft", "priv"} <= _ids(site)
