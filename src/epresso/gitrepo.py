"""One repository adapter for epresso.

Canonical home for git *discovery* — reading a repo's origin URL and default
branch — so ``config.py`` (site.repository/branch defaults) and ``docsgen.py``
(docs-source edit links) don't each re-implement it. Cloning theme repos stays in
``themes.py`` (decision G11/G12) and is out of scope here.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git(repo_dir: Path, *args: str) -> str:
    """Run ``git -C repo_dir``; return trimmed stdout or ``""``."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_dir), *args],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:  # noqa: BLE001 - git missing/fails
        return ""


def normalize_repo_url(url: str) -> str:
    """Turn a git remote URL into an https:// web URL (no trailing ``.git``)."""
    url = url.strip()
    if url.endswith(".git"):
        url = url[:-4]
    if url.startswith("git@"):
        url = url.replace(":", "/").replace("git@", "https://")
    elif url.startswith("git://"):
        url = "https://" + url[len("git://") :]
    return url.rstrip("/")


def origin_url(repo_dir: Path) -> str:
    """Return a repo's ``origin`` remote URL (https-normalized), or ``""``."""
    url = _git(repo_dir, "remote", "get-url", "origin")
    if not url:
        cfg = repo_dir / ".git" / "config"
        if cfg.is_file():
            try:
                import configparser  # noqa: PLC0415

                cp = configparser.ConfigParser()
                cp.read(cfg)
                url = cp.get('remote "origin"', "url", fallback="")
            except Exception:  # noqa: BLE001
                return ""
    return normalize_repo_url(url) if url else ""


def default_branch(repo_dir: Path) -> str:
    """A repo's default branch: ``origin/HEAD`` if recorded, else the checked-out
    branch. Returns ``""`` when unknown."""
    ref = _git(repo_dir, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if ref:
        return ref.split("/", 1)[-1] if ref.startswith("origin/") else ref
    cur = _git(repo_dir, "symbolic-ref", "--short", "HEAD")
    return "" if cur == "HEAD" else cur  # detached HEAD
