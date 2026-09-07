"""epresso error model — rich, typed errors with file:line context and fix suggestions."""

from __future__ import annotations


class EpressoError(Exception):
    """Base error. Carries a location (path:line) and an optional fix suggestion."""

    category = "error"
    fix: str | None = None

    def __init__(
        self,
        message: str,
        *,
        path: str | None = None,
        line: int | None = None,
        fix: str | None = None,
    ) -> None:
        self.message = message
        self.path = path
        self.line = line
        if fix is not None:
            self.fix = fix
        super().__init__(self.__str__())

    def __str__(self) -> str:
        loc = ""
        if self.path:
            loc = f"{self.path}"
            if self.line:
                loc += f":{self.line}"
            loc = f" ({loc})"
        s = f"{self.category}: {self.message}{loc}"
        if self.fix:
            s += f"\n  💡 {self.fix}"
        return s


class ConfigError(EpressoError):
    category = "config error"


class ContentError(EpressoError):
    category = "content error"


class RouteError(EpressoError):
    category = "route error"


class TemplateError(EpressoError):
    category = "template error"


class BuildError(EpressoError):
    category = "build error"


class PluginError(EpressoError):
    category = "plugin error"
