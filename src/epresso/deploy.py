"""Deployment — `epresso deploy` static hosting providers.

GitHub Pages: build the site, copy ``dist/`` into a fresh temporary repo, commit,
and force-push to a branch (default ``gh-pages``). No external API keys required —
only git and push access to the remote.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

PROVIDERS = ("gh-pages",)


def gh_pages(site: Any, *, remote: str = "origin", branch: str = "gh-pages", push: bool = True) -> str:
    site.build(clean=True)
    dist = site.config.dir_output()
    if not dist.exists() or not any(dist.iterdir()):
        raise RuntimeError("build produced no output")

    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is required for gh-pages deploy")

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "site"
        subprocess.run([git, "init", "-q", str(repo)], check=True)
        _copy_contents(dist, repo)
        subprocess.run([git, "add", "-A"], cwd=repo, check=True)
        env = {
            **__import__("os").environ,
            "GIT_AUTHOR_NAME": "epresso deploy",
            "GIT_AUTHOR_EMAIL": "deploy@epresso.local",
            "GIT_COMMITTER_NAME": "epresso deploy",
            "GIT_COMMITTER_EMAIL": "deploy@epresso.local",
        }
        subprocess.run([git, "commit", "-q", "-m", "deploy"], cwd=repo, env=env, check=True)
        if push:
            subprocess.run([git, "remote", "add", "origin", remote], cwd=repo, check=True)
            subprocess.run([git, "push", "-f", "origin", f"HEAD:{branch}"], cwd=repo, check=True)

    verb = "pushed" if push else "built (not pushed)"
    return f"Deployed {len(list(dist.rglob('*')))} files to {remote}/{branch} ({verb})"


def _copy_contents(src: Path, dst: Path) -> None:
    for f in src.rglob("*"):
        if f.is_file():
            rel = f.relative_to(src)
            out = dst / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, out)
