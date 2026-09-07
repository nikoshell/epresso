"""Pipeline helpers shared by the asset, image and script-bundle emitters.

Each pipeline (``assets``, ``images``, ``render``) writes outputs into ``dist/``,
and each independently re-implemented two fiddly things: hashing a source file,
and running the external ``esbuild`` binary with a graceful fallback when it is
absent or fails (JS stays optional). Both live here so the behaviour is defined
once and each emitter keeps only its own fallback policy.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Literal

__all__ = ["bundle_js", "file_digest"]

BundleResult = Literal["ok", "missing", "failed"]


def file_digest(path: Path, length: int | None = None) -> str:
    """SHA-256 of a file's bytes, optionally truncated to ``length`` hex chars.

    ``length=None`` returns the full digest; the callers choose their own
    truncation (12 chars for hashed asset URLs, 10 for image variants).
    """
    with path.open("rb") as fh:
        d = hashlib.file_digest(fh, "sha256").hexdigest()
    return d if length is None else d[:length]


def bundle_js(
    sources: list[str],
    *,
    outfile: Path | None = None,
    outdir: Path | None = None,
    entry_names: str | None = None,
    minify: bool = False,
) -> tuple[BundleResult, str]:
    """Bundle JS ``sources`` with esbuild.

    Returns ``(result, detail)`` where ``result`` is:

    * ``"ok"`` — esbuild ran and wrote the output(s);
    * ``"missing"`` — esbuild is not on PATH (``detail`` is empty);
    * ``"failed"`` — esbuild errored (``detail`` is its stderr).

    The caller owns the fallback policy (write raw JS, copy verbatim, warn), so
    the three emitters keep their distinct behaviour while sharing the run/error
    handling. Exactly one of ``outfile`` (single entry → one output) or
    ``outdir`` (multiple entries) is used.
    """
    esbuild = shutil.which("esbuild")
    if not esbuild:
        return "missing", ""
    args = [esbuild, *sources]
    if minify:
        args.append("--minify")
    args += ["--bundle", "--format=esm"]
    if outfile is not None:
        args.append(f"--outfile={outfile}")
    if outdir is not None:
        args.append(f"--outdir={outdir}")
    if entry_names:
        args.append(f"--entry-names={entry_names}")
    try:
        subprocess.run(args, check=True, capture_output=True, text=True)
        return "ok", ""
    except subprocess.CalledProcessError as e:
        return "failed", e.stderr.strip()
