"""CSS processing — PostCSS / Tailwind support.

Tailwind v4 and most modern CSS tooling run on PostCSS/LightningCSS rather than
esbuild. This module detects a PostCSS or Tailwind setup in the project and, when
the corresponding external binary is available, runs it on declared CSS entry
points. Otherwise it falls back to a verbatim copy so CSS stays optional.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


class CSSProcessor:
    def __init__(self, config: Any) -> None:
        self.config = config
        self._detected = self._detect()
        self._warnings: list[str] = []

    def _bin(self, name: str) -> str | None:
        """Locate a build binary — project-local ``node_modules/.bin`` first, then PATH.

        This makes Tailwind/PostCSS processing work regardless of the shell PATH
        (e.g. under systemd-run or CI where global npm bins may not be on PATH).
        """
        local = self.config.root / "node_modules" / ".bin" / name
        if local.is_file():
            return str(local)
        return shutil.which(name)

    def _detect(self) -> tuple[str, Path] | None:
        """Return ``('postcss'|'tailwind', config_path)`` when usable, else None.

        Also resolves the binary path into ``self._cmd`` so ``process`` doesn't
        depend on the shell PATH.
        """
        root = self.config.root
        self._cmd = None
        postcss_cfg = next(root.glob("postcss.config.*"), None)
        if postcss_cfg and self._bin("postcss"):
            self._cmd = self._bin("postcss")
            return ("postcss", postcss_cfg)
        tailwind_cfg = next(root.glob("tailwind.config.*"), None)
        if tailwind_cfg and self._bin("tailwindcss"):
            self._cmd = self._bin("tailwindcss")
            return ("tailwind", tailwind_cfg)
        # Tailwind v4: no config file required, but only auto-detect when the
        # project has its own CLI (node_modules/.bin/tailwindcss) — NOT a global
        # PATH binary — so a project that doesn't use Tailwind isn't misdetected.
        local_tw = root / "node_modules" / ".bin" / "tailwindcss"
        if local_tw.is_file():
            self._cmd = str(local_tw)
            return ("tailwind", root / "tailwind.config.js")
        return None

    @property
    def active(self) -> bool:
        return self._detected is not None

    @property
    def minifies(self) -> bool:
        """Whether the detected processor already minifies its output.

        The tailwind standalone CLI is invoked with ``--minify``; the postcss path
        runs the project's plugins, which minify only if the project says so.
        """
        return bool(self._detected and self._detected[0] == "tailwind")

    def process(self, entry_src: Path, out_dir: Path) -> Path | None:
        """Process ``entry_src`` → an output path under ``out_dir``, or None to fall back."""
        if not self._detected or self._cmd is None:
            return None
        kind, cfg = self._detected
        rel = entry_src.relative_to(self.config.dir_assets())
        out = out_dir / "assets" / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            if kind == "postcss":
                subprocess.run(
                    [self._cmd, str(entry_src), "-o", str(out), "--config", str(cfg)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:  # tailwind standalone
                subprocess.run(
                    [self._cmd, "-i", str(entry_src), "-o", str(out), "--minify"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
        except subprocess.CalledProcessError as e:
            self._warnings.append(f"CSS processing failed for {entry_src.name}: {e.stderr.strip()}")
            return None
        return out

    @property
    def warnings(self) -> list[str]:
        return self._warnings
