"""Reject legacy Jinja *composition* directives in ``.ep`` author files.

epresso components (``<Card>…</Card>``, ``<slot/>``, layout components) are the
blessed way to compose pages and layouts. Jinja directives that used to do that
job (``extends``/``block``/``include``/``import``/``macro``/``component``) are
forbidden in ``.ep`` authoring and fail the build by default, so a theme can't
silently drift back to Jinja composition.

This is deliberately *not* a full Jinja ban: ``{{ expr }}`` interpolation, JSX
``{expr}`` props, ``{% if %}``/``{% for %}`` control flow and comments stay
allowed (the engine still renders through Jinja, and there is no component
equivalent for conditionals/loops yet). Only the composition forms — the ones a
component/``<slot/>`` already replaces — are rejected. Legacy ``.html``
templates are exempt.
"""

from __future__ import annotations

import re
from typing import NoReturn

from .errors import TemplateError

# Directives with a components/<slot/> replacement. Authors must reach for
# <X />, <slot/> and layout components instead.
_FORBIDDEN: frozenset[str] = frozenset(
    {
        "extends",
        "block",
        "include",
        "import",
        "from",
        "macro",
        "component",
        "call",
    }
)

# A statement tag's leading directive: `{% name %}` / `{%- name ... %}`.
_DIRECTIVE = re.compile(r"\{%\s*-?\s*([A-Za-z_][A-Za-z0-9_]*)\b")

# Regions to ignore entirely: Jinja comments and HTML comments (a commented-out
# tag must not trip enforcement).
_COMMENT = re.compile(r"\{#.*?#\}|<!--.*?-->", re.DOTALL)


def composition_violations(body: str) -> list[tuple[str, int]]:
    """Return ``[(directive, line)]`` for forbidden Jinja directives in ``body``.

    ``body`` is the parsed ``.ep`` body *after* ``<style>/<script>`` extraction,
    so Jinja inside scripts/styles is not scanned (and comments/expressions with
    a ``{%`` are naturally not matched because they lack a directive name).
    """
    out: list[tuple[str, int]] = []
    scan = _COMMENT.sub("", body)
    for m in _DIRECTIVE.finditer(scan):
        directive = m.group(1)
        if directive in _FORBIDDEN:
            lineno = scan.count("\n", 0, m.start()) + 1
            out.append((directive, lineno))
    return out


def ensure_components(body: str, label: str) -> None:
    """Raise :class:`epresso.errors.TemplateError` on any forbidden directive.

    ``label`` is a human/path label for the file (shown in the error location).
    """
    violations = composition_violations(body)
    if not violations:
        return
    _raise_first(violations, label)


def _raise_first(violations: list[tuple[str, int]], label: str) -> NoReturn:
    directives = ", ".join(f"{{% {d} %}}" for d, _line in violations)
    first_line = violations[0][1]
    raise TemplateError(
        f"legacy Jinja composition used — {directives} are not allowed in .ep "
        "files; compose with components and <slot/> instead",
        path=label,
        line=first_line,
        fix="replace {% extends %}/{% block %} with a layout component + <slot/>, "
        "{% include %}/{% component %} with <Component/>, {% macro %}/{% import %} "
        "with a component (see docs). .ep control flow ({% if %}/{% for %}) and "
        "{{ expr }} stay allowed.",
    )
