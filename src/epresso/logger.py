"""epresso logger — level-gated, ``EPRESSO_DEBUG``-scoped, colored labels.

Levels: ``debug`` < ``info`` < ``warn`` < ``error``. ``info``/``warn``/``error``
always emit (subject to a min level); ``debug`` is gated by the ``EPRESSO_DEBUG``
env var, e.g. ``EPRESSO_DEBUG=build`` or ``EPRESSO_DEBUG=*`` for everything.

Each logger has a scope name shown as a colored ``[scope]`` label, so output
reads ``[build] …``, ``[content] …`` sections.
"""

from __future__ import annotations

import atexit
import os
import sys

_LEVELS = {"debug": 10, "info": 20, "warn": 30, "error": 40}
_COLORS = {"debug": "\x1b[90m", "info": "\x1b[36m", "warn": "\x1b[33m", "error": "\x1b[31m"}
_RESET = "\x1b[0m"

# Optional file sink: set ``EPRESSO_LOG=<path>`` to also append logs to a file.
_log_file = None  # type: ignore


def _open_log_file() -> None:
    global _log_file
    path = os.environ.get("EPRESSO_LOG", "").strip()
    if not path:
        _log_file = None
        return
    try:
        _log_file = open(path, "a", encoding="utf-8")  # noqa: SIM115
        atexit.register(_log_file.close)
    except OSError:
        _log_file = None


_open_log_file()


def _debug_scopes() -> set[str]:
    val = os.environ.get("EPRESSO_DEBUG", "").strip()
    return {s.strip() for s in val.split(",") if s.strip()} if val else set()


def _color() -> bool:
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


class Logger:
    """A named logger. ``debug`` is gated by ``EPRESSO_DEBUG`` scopes."""

    def __init__(self, name: str):
        self.name = name
        self._level = _LEVELS["info"]

    def _enabled(self, level: str) -> bool:
        if level == "debug":
            # debug is gated by EPRESSO_DEBUG scopes, not the min level
            scopes = _debug_scopes()
            return bool(scopes) and (
                "*" in scopes
                or self.name in scopes
                or any(self.name.startswith(s + ":") for s in scopes)
            )
        return _LEVELS[level] >= self._level

    def _emit(self, level: str, msg: str) -> None:
        if not self._enabled(level):
            return
        out = sys.stdout if level in ("debug", "info") else sys.stderr
        label = f"{_COLORS[level]}[{self.name}]{_RESET}" if _color() else f"[{self.name}]"
        out.write(f"{label} {msg}\n")
        out.flush()
        if _log_file is not None:
            _log_file.write(f"[{self.name}] {msg}\n")
            _log_file.flush()

    def debug(self, msg: str) -> None:
        self._emit("debug", msg)

    def info(self, msg: str) -> None:
        self._emit("info", msg)

    def warn(self, msg: str) -> None:
        self._emit("warn", msg)

    def error(self, msg: str) -> None:
        self._emit("error", msg)


def get_logger(name: str = "epresso") -> Logger:
    """Return a logger for a scope (``build``, ``content``, ``render``, ``cli``, …)."""
    return Logger(name)


log = get_logger("epresso")
