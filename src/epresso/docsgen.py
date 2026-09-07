"""``epresso docs`` scaffolding — build a minimal docs project from a bare dir.

The ``docs`` CLI command needs to turn an arbitrary Markdown/git-repo directory
into a renderable epresso project. That logic (repo detection, git remote
normalisation, docs-content copying, site.toml patching) is not CLI wiring, so
it lives here behind a small interface instead of inside ``cli.py``.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path

from .gitrepo import default_branch as repo_default_branch  # noqa: F401  (re-export)
from .gitrepo import normalize_repo_url  # noqa: F401  (re-export)
from .gitrepo import origin_url as repo_origin

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", ".next"}


def is_repo_dir(source: Path) -> bool:
    """True when ``source`` is a git checkout or contains git repos (any depth).

    Used to decide whether to copy only the documentation markdown (docs/ +
    top-level READMEs) rather than the whole checkout.
    """
    if (source / ".git").exists():
        return True
    for _root, dirs, _files in os.walk(source):
        if ".git" in dirs:
            return True
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    return False


def copy_docs_content(source: Path, dst: Path, docs_dir: str = "docs") -> dict[str, dict[str, str]]:
    """Copy ``source`` into ``dst`` for the docs collection (single repo).

    For a repo dir (see :func:`is_repo_dir`), copy the markdown under the
    ``docs_dir`` subdirectory (default ``docs/``, overridable via ``REPO_DOCS``)
    plus a ``README`` at the repo root, skipping build/source junk, and write a
    ``.git`` marker at ``dst`` so the theme can detect the single repo root.
    Bare markdown dirs keep the full copy.

    Returns ``{}`` (kept for back-compat; no multi-repo map).
    """
    dst.mkdir(parents=True, exist_ok=True)
    repo_mode = is_repo_dir(source)
    for root, dirs, files in os.walk(source):
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and (d == docs_dir or not d.startswith("_"))
        ]
        rel = Path(root).relative_to(source)
        for fn in files:
            if fn.startswith("_"):
                continue  # _-prefixed (private/draft) files are excluded from processing
            src_f = Path(root) / fn
            if src_f.is_symlink() and not src_f.exists():
                continue  # broken symlink
            if not repo_mode:
                # bare dir: copy everything (skip junk + broken symlinks)
                out = dst / rel / fn
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_f, out)
                continue
            name = fn.lower()
            rel_parts = rel.parts
            under_docs = bool(rel_parts and rel_parts[0] == docs_dir)
            root_readme = rel_parts == () and (name.startswith("readme") or name == "readme.txt")
            is_md = name.endswith((".md", ".markdown"))
            if not (under_docs or root_readme):
                continue
            if not is_md and not root_readme:
                # non-markdown files are docs assets (images etc.) only under the
                # docs dir; keep them so relative image srcs resolve.
                if not under_docs:
                    continue
            # docs-dir content lands under dst relative to docs_dir (no nesting),
            # so doc ids / image paths stay relative to the docs base.
            rel_dst = rel.relative_to(docs_dir) if under_docs else rel
            out = dst / rel_dst / fn
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_f, out)
    if repo_mode:
        # single-repo: mark the docs root as the repo (so the theme can detect
        # the root and the README there gets a git icon).
        (dst / ".git").mkdir(parents=True, exist_ok=True)
    return {}


def copy_docs_assets(source: Path, public_base: Path, docs_dir: str) -> None:
    """Mirror non-markdown assets under ``source/<docs_dir>`` to ``public_base``.

    Docs relative image srcs are rewritten to ``/content/<docs_dir>/...``; publishing
    the assets under the project's ``public/content/<docs_dir>`` (copied verbatim to
    the output root) makes those URLs resolve.
    """
    base = source / docs_dir
    if not base.is_dir():
        return
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith("_")]
        rel = Path(root).relative_to(base)
        for fn in files:
            if fn.startswith("_") or fn.lower().endswith((".md", ".markdown")):
                continue
            src_f = Path(root) / fn
            if src_f.is_symlink() and not src_f.exists():
                continue
            out = public_base / rel / fn
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_f, out)


def auto_docs_project(source: Path, port: int, theme: Path | None = None) -> Path:
    """Build a temp epresso project that renders a bare Markdown dir.

    Defaults to the bundled ``themes/docs`` theme (or a custom ``theme``). The
    theme project is copied and the source is injected as its ``content/docs``
    collection content, so it renders fully with the docs theme.
    """
    if theme is None:
        theme = Path(__file__).resolve().parent.parent.parent / "themes" / "docs"
    theme = theme.resolve()
    tmp = Path(tempfile.mkdtemp(prefix="epresso-docs-"))
    for item in theme.iterdir():
        if item.name in (".cache", "dist", "__pycache__", "content"):
            continue
        dst = tmp / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy(item, dst)
    (tmp / "content").mkdir(exist_ok=True)
    docs_dir = os.environ.get("EPRESSO_DOCS_DIR") or os.environ.get("REPO_DOCS") or _theme_option(theme, "docs_dir", "docs")
    docs_dir = docs_dir.strip("/") or "docs"
    docs_dir_path = tmp / "content" / "docs"
    copy_docs_content(source, docs_dir_path, docs_dir=docs_dir)
    # Publish docs image assets at their /content/<docs_dir>/... URL.
    copy_docs_assets(source, tmp / "public" / "content" / docs_dir, docs_dir)
    # Point the theme's docs collection at the copy via site.toml (no env).
    patch_site_toml(tmp, port, source, docs_base=docs_dir_path.resolve())
    return tmp


def _theme_option(theme: Path, name: str, default: str = "") -> str:
    """Read a ``[theme]`` option from the theme's ``site.toml`` (pre-copy)."""
    try:
        import tomllib

        cfg = tomllib.loads((theme / "site.toml").read_text(encoding="utf-8"))
        return str(cfg.get("theme", {}).get(name, default))
    except Exception:  # noqa: BLE001
        return default


def patch_site_toml(tmp: Path, port: int, source: Path, docs_base: Path | None = None) -> None:
    """Point a copied theme's ``[site] url`` at the local preview host, record
    the docs source path (``docs_source``), and override the docs base
    (``[theme] docs_base``) so the theme reads the copied content."""
    p = tmp / "site.toml"
    if not p.exists():
        return
    s = p.read_text(encoding="utf-8")
    s = re.sub(r'url\s*=\s*"[^"]*"', f'url = "http://127.0.0.1:{port}"', s, count=1)
    if "docs_source" not in s:
        path = str(source).replace("\\", "\\\\").replace('"', '\\"')
        s = s.replace("[site]\n", f'[site]\ndocs_source = "{path}"\n', 1)
    if docs_base is not None:
        path = str(docs_base).replace("\\", "\\\\").replace('"', '\\"')
        if re.search(r"(?m)^\[theme\]\s*$", s):
            if re.search(r"(?m)^docs_base\s*=", s):
                s = re.sub(r"(?m)^docs_base\s*=.*$", f'docs_base = "{path}"', s, count=1)
            else:
                s = re.sub(r"(?m)^\[theme\]\s*$", f'[theme]\ndocs_base = "{path}"', s, count=1)
        else:
            s += f'\n[theme]\ndocs_base = "{path}"\n'
    # point the GitHub link at the source repo, not the theme's own.
    origin = repo_origin(source)
    if origin:
        s = re.sub(r"(?m)^\s*repository\s*=.*$", f'repository = "{origin}"', s, count=1)
        if "repository" not in s:
            s = s.replace("[site]\n", f'[site]\nrepository = "{origin}"\n', 1)
    # ... and its default branch (the theme's site.toml defaults to "main").
    branch = repo_default_branch(source)
    if branch:
        if re.search(r"(?m)^\s*branch\s*=.*$", s):
            s = re.sub(r"(?m)^\s*branch\s*=.*$", f'branch = "{branch}"', s, count=1)
        else:
            s = s.replace("[site]\n", f'[site]\nbranch = "{branch}"\n', 1)
    p.write_text(s, encoding="utf-8")
