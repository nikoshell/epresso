"""Theme registry — built-in name → repo, plus `epresso new` scaffolding.

Themes are git-cloned from separate repos. ``epresso new`` accepts three source
forms:

* a **registry name** (``docs``, ``blog``) — resolved from :data:`REGISTRY`;
* a **git URL** — ``https://…``, ``ssh://…``, ``git@host:owner/repo``, or the
  ``github:owner/repo`` shorthand — optionally with a trailing ``@ref`` for a
  branch or tag;
* a **directory path** to an existing theme checkout.

A source resolves as: local directory copy → git clone. A registry name with
neither available falls back to a bundled starter shipped in the package.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# name -> (repo path or URL, default branch).
# Themes that ship in this repository live under ``themes/``. Other names are
# resolved from a sibling checkout (dev) or a published git URL.
_REPO = Path(__file__).resolve().parents[2]
REGISTRY: dict[str, tuple[str, str]] = {
    "docs": (str(_REPO / "themes" / "docs"), "main"),
    "blog": (str(Path(__file__).resolve().parents[3] / "epresso-theme-blog"), "main"),
}

_GIT_PREFIXES = ("http://", "https://", "git://", "ssh://", "file://", "git@")


def bundled_starter(name: str) -> Path | None:
    """Return the bundled starter dir for a theme, if it ships one."""
    p = Path(__file__).parent / "themes" / name
    return p if p.is_dir() else None


def list_themes() -> list[str]:
    return sorted(REGISTRY)


def parse_source(source: str) -> tuple[str, str | None] | None:
    """Resolve a non-registry ``source`` to ``(repo, ref)``, or ``None``.

    ``repo`` is a path or clone URL; ``ref`` is a branch/tag, or ``None`` to use
    the repository's default branch. Accepts a git URL, a ``git@`` scp-style
    path, or a ``github:owner/repo`` shorthand (each with an optional ``@ref``),
    or an existing local directory.
    """
    head = source[4:] if source.startswith("git+") else source
    if head.startswith("github:"):
        head = "https://github.com/" + head[len("github:") :]
    if head.startswith(_GIT_PREFIXES):
        return _split_ref(head)
    local = Path(source).expanduser()
    if local.is_dir():
        return str(local), None
    return None


def _split_ref(url: str) -> tuple[str, str | None]:
    """Split a trailing ``@ref`` off a git URL.

    Only the last path segment is inspected, so ``git@host:owner/repo`` (whose
    userinfo contains an ``@``) is never mistaken for a ref.
    """
    if "@" in url.rsplit("/", 1)[-1]:
        repo, _, ref = url.rpartition("@")
        return repo, ref or None
    return url, None


def _looks_like_path(source: str) -> bool:
    return source.startswith((".", "/", "~")) or "/" in source or "\\" in source


def scaffold(source: str, dest: Path) -> str:
    """Create a project at ``dest`` from theme ``source`` (copy/clone, else bundled)."""
    from_registry = source in REGISTRY
    if from_registry:
        repo, ref = REGISTRY[source]
    else:
        parsed = parse_source(source)
        if parsed is None:
            if _looks_like_path(source):
                raise FileNotFoundError(f"theme directory {source!r} does not exist")
            names = ", ".join(list_themes())
            raise KeyError(f"unknown theme {source!r}; expected a name ({names}), a git URL, or a directory")
        repo, ref = parsed
    dest.mkdir(parents=True, exist_ok=True)

    used: str | None = None
    local = Path(repo).expanduser()
    if local.is_dir():
        # prefer a local theme repo (development); strip its git history
        _copy_tree(local, dest)
        _strip_git(dest)
        used = f"copied from {local}"
    else:
        git = shutil.which("git")
        if git and not any(dest.iterdir()):
            cmd = [git, "clone", "--depth=1"]
            if ref:
                cmd += ["--branch", ref]
            cmd += [repo, str(dest)]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                _strip_git(dest)
                used = f"cloned {repo}"
            except (subprocess.CalledProcessError, OSError):
                used = None

    if used is None:
        # Only a registry name can fall back to a bundled starter.
        starter = bundled_starter(source) if from_registry else None
        if starter is None:
            raise FileNotFoundError(f"could not fetch theme {source!r} (no local directory; git clone failed)")
        _copy_tree(starter, dest)
        used = "bundled starter"

    return f"Scaffolded theme {source!r} ({used}) → {dest}"


# Build outputs and the incremental cache are never part of a scaffolded theme.
_SKIP_DIRS = frozenset({".git", "__pycache__", "dist", ".cache"})


def _copy_tree(src: Path, dst: Path) -> None:
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        if _SKIP_DIRS.intersection(f.parts):
            continue
        rel = f.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, out)


def _strip_git(dest: Path) -> None:
    gitdir = dest / ".git"
    if gitdir.exists():
        shutil.rmtree(gitdir)
