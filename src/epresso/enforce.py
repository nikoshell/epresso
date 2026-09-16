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
component/``<slot/>`` already replaces — are rejected. Only ``.ep`` files are
checked; there is no Jinja-template page format left to exempt.

The module also owns the **.ep file-shape** rule (:func:`ensure_ep_structure`):
an ``.ep`` template renders at most one root per branch (a branch may render
nothing), and its sidecar blocks are capped at one scoped ``<style>``, one
``<style is:global>`` and one ``<script>``. ``.ep`` endpoints (whose body is
never rendered) are exempt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NoReturn

from .document import line_at
from .errors import TemplateError

if TYPE_CHECKING:
    from .document import Document, SidecarBlocks

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


# ── .ep file shape: at most one root per branch, capped sidecars ──────────

# Real HTML void elements. Matched only when written lowercase: component tags
# are Capitalized, so <Base>/<Link>/<Source> must not look like <base>/<link>.
_VOID_TAGS = frozenset(
    "area base br col embed hr img input link meta param source track wbr".split()
)
_HTML_TAG = re.compile(r"<\s*(/?)\s*([A-Za-z][-\w:]*)([^>]*?)(/?)\s*>", re.DOTALL)
_SIDECAR_BLOCK = re.compile(r"<(style|script)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)
_JINJA_NAME = re.compile(r"\{%-?\s*([A-Za-z_]+)")

_ROOT_FIX = (
    "an .ep file renders at most one root per branch: wrap siblings in "
    "<Fragment>…</Fragment> (or <></>); a branch that renders nothing needs no marker"
)
_SIDECAR_FIX = (
    "one scoped <style>, one <style is:global> and one <script> per .ep file — "
    "merge same-kind blocks"
)


@dataclass
class _Frame:
    """One branch scope and the roots that emit output inside it."""

    kind: str
    line: int
    roots: list[tuple[int, str]] = field(default_factory=list)

    def add(self, line: int, what: str) -> None:
        self.roots.append((line, what))


def _frame_violations(frame: _Frame, where: str) -> list[tuple[int, str]]:
    """``[(line, message)]`` unless the frame renders exactly one root."""
    if len(frame.roots) == 1:
        return []
    if not frame.roots:
        return [(frame.line, f"{where} renders no root — add an element or <></>")]
    nodes = ", ".join(what for _line, what in frame.roots)
    return [
        (
            frame.roots[1][0],
            f"{len(frame.roots)} roots in the same branch: {nodes} — wrap them in "
            "<Fragment>…</Fragment> or <></>",
        )
    ]


def structure_violations(body: str) -> list[tuple[int, str]]:
    """Return ``[(line, message)]`` for .ep file-shape violations in ``body``.

    Every branch of an .ep template renders at most one root — an element, a
    component, ``<Fragment>``/``<>``, ``<slot/>``, an interpolation or text.
    Whitespace and comments emit nothing and are ignored. ``{% if %}`` and
    ``{% for %}`` introduce branches, each checked recursively. An implicit
    ``{% if %}`` branch (no ``{% else %}``) renders nothing, which is fine —
    like a ``{% for %}`` over an empty sequence. Only a branch that *does*
    render something must render exactly one root.
    """
    text = _COMMENT.sub("", _SIDECAR_BLOCK.sub("", body))
    out: list[tuple[int, str]] = []
    root = _Frame("root", 1)
    frame = root
    conds: list[dict] = []
    loops: list[dict] = []
    depth = 0
    i, n = 0, len(text)
    while i < n:
        if text.startswith("{{", i):
            j = text.find("}}", i)
            j = n if j < 0 else j + 2
            if depth == 0:
                frame.add(line_at(text, i), "{{ … }}")
            i = j
        elif text.startswith("{%", i):
            j = text.find("%}", i)
            j = n if j < 0 else j + 2
            m = _JINJA_NAME.match(text, i)
            name = m.group(1) if m else ""
            line = line_at(text, i)
            if depth == 0:
                if name == "if":
                    cond = {
                        "line": line,
                        "parent": frame,
                        "frames": [_Frame("if", line)],
                    }
                    conds.append(cond)
                    frame = cond["frames"][0]
                elif name in ("elif", "else"):
                    if conds:
                        cond = conds[-1]
                        branch = _Frame(name, line)
                        cond["frames"].append(branch)
                        frame = branch
                elif name == "endif":
                    if conds:
                        cond = conds.pop()
                        for branch in cond["frames"]:
                            out += _frame_violations(branch, f"the {{% {branch.kind} %}} branch")
                        frame = cond["parent"]
                        frame.add(cond["line"], "{% if %}")
                elif name == "for":
                    loop = {"line": line, "parent": frame, "body": _Frame("for", line)}
                    loops.append(loop)
                    frame = loop["body"]
                elif name == "endfor":
                    if loops:
                        loop = loops.pop()
                        out += _frame_violations(loop["body"], "the {% for %} body")
                        frame = loop["parent"]
                        frame.add(loop["line"], "{% for %}")
            i = j
        elif text.startswith("<>", i):
            # Zero-output group shorthand — the group itself is the root, and its
            # contents are one level deeper.
            if depth == 0:
                frame.add(line_at(text, i), "<></>")
            depth += 1
            i += 2
        elif text.startswith("</>", i):
            depth = max(0, depth - 1)
            i += 3
        elif text[i] == "<":
            j = text.find(">", i)
            if j < 0:
                break
            m = _HTML_TAG.match(text, i)
            if m is not None:
                closing, name, self_closing = m.group(1), m.group(2), m.group(4)
                if closing:
                    depth = max(0, depth - 1)
                else:
                    if depth == 0:
                        frame.add(line_at(text, i), f"<{name}>")
                    if not (self_closing or (name.islower() and name in _VOID_TAGS)):
                        depth += 1
            i = j + 1
        else:
            nxt = [
                p
                for p in (text.find("<", i), text.find("{%", i), text.find("{{", i))
                if p >= 0
            ]
            j = min(nxt) if nxt else n
            if depth == 0 and text[i:j].strip():
                frame.add(line_at(text, i), "text")
            i = j
    out += _frame_violations(root, "the file")
    out.sort(key=lambda v: v[0])
    return out


def sidecar_violations(sidecars: SidecarBlocks) -> list[tuple[int, str]]:
    """``[(line, message)]`` when a sidecar kind has more than one block."""
    out: list[tuple[int, str]] = []
    for lines, label in (
        (sidecars.scoped_styles, "scoped <style>"),
        (sidecars.global_styles, "<style is:global>"),
        (sidecars.scripts, "<script>"),
    ):
        if len(lines) > 1:
            out.append((lines[1], f"{len(lines)} {label} blocks — merge them into one"))
    return out


def ensure_ep_structure(doc: Document, label: str) -> None:
    """Raise :class:`TemplateError` when an .ep file breaks the file-shape contract.

    Called where a .ep body is about to be rendered (components and pages), so
    endpoint .ep files that only return generated content are never checked.
    Reported lines are file-relative (the parser's front-matter offset is added).
    """
    offset = doc.line_offset
    root_problems = [(line + offset, msg) for line, msg in structure_violations(doc.body)]
    sidecar_problems = [(line + offset, msg) for line, msg in sidecar_violations(doc.sidecars)]
    violations = sorted(root_problems + sidecar_problems, key=lambda v: v[0])
    if not violations:
        return
    detail = "\n".join(f"    line {line}: {msg}" for line, msg in violations)
    fix = "; ".join(
        part
        for part in (
            _ROOT_FIX if root_problems else "",
            _SIDECAR_FIX if sidecar_problems else "",
        )
        if part
    )
    raise TemplateError(
        f"invalid .ep file shape — {len(violations)} problem(s):\n{detail}",
        path=label,
        line=violations[0][0],
        fix=fix,
    )
