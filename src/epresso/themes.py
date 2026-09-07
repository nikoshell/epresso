"""Theme registry — built-in name → repo, plus `epresso new` scaffolding.

Per decision G11/G12, themes are git-cloned from separate repos. The registry
value may be a local path (dev) or a remote URL (published). ``scaffold``
resolves in order: local repo copy → git clone → bundled starter fallback.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# name -> (repo path or URL, default branch)
# Local dev: sibling theme repos next to the epresso repo. Published: swap to GitHub URLs.
REGISTRY: dict[str, tuple[str, str]] = {
    "docs": (str(Path(__file__).resolve().parents[3] / "epresso-theme-docs"), "main"),
    "blog": (str(Path(__file__).resolve().parents[3] / "epresso-theme-blog"), "main"),
}


def bundled_starter(name: str) -> Path | None:
    """Return the bundled starter dir for a theme, if it ships one."""
    p = Path(__file__).parent / "themes" / name
    return p if p.is_dir() else None


def list_themes() -> list[str]:
    return sorted(REGISTRY)


def scaffold(name: str, dest: Path) -> str:
    """Create a project at ``dest`` from theme ``name`` (copy/clone, else bundled)."""
    if name not in REGISTRY:
        raise KeyError(f"unknown theme {name!r}; available: {', '.join(list_themes())}")
    repo, branch = REGISTRY[name]
    dest.mkdir(parents=True, exist_ok=True)

    used: str | None = None
    local = Path(repo)
    if local.is_dir():
        # prefer a local theme repo (development); strip its git history
        _copy_tree(local, dest)
        _strip_git(dest)
        used = f"copied from {local}"
    else:
        git = shutil.which("git")
        if git and not any(dest.iterdir()):
            try:
                subprocess.run(
                    [git, "clone", "--depth=1", "--branch", branch, repo, str(dest)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                _strip_git(dest)
                used = f"cloned {repo}"
            except (subprocess.CalledProcessError, OSError):
                used = None

    if used is None:
        starter = bundled_starter(name)
        if starter is None:
            raise FileNotFoundError(f"no bundled starter for theme {name!r} and clone failed")
        _copy_tree(starter, dest)
        used = "bundled starter"

    return f"Scaffolded theme {name!r} ({used}) → {dest}"


def _copy_tree(src: Path, dst: Path) -> None:
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        if ".git" in f.parts or "__pycache__" in f.parts:
            continue
        rel = f.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, out)


def _strip_git(dest: Path) -> None:
    gitdir = dest / ".git"
    if gitdir.exists():
        shutil.rmtree(gitdir)
