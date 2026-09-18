"""JSX-style attribute parsing — shared by the template JSX rewrite and the
markdown component-tag pass.

Both consumers parse the same grammar — ``key="v"``, ``key='v'``, ``key={expr}``
and a bare ``key`` — but shape the result differently: the template JSX rewrite
turns it into ``{% component %}`` kwargs, the markdown pass into a dict of props.
This module owns the grammar once; each caller keeps only its output-shaping
shim.
"""

from __future__ import annotations

import re
from typing import Any

__all__ = ["Expr", "parse_jsx_attrs"]


class Expr(str):
    """A braced ``{expr}`` attribute value.

    A ``str`` subclass so it behaves as text, but distinguishable from a
    quoted-string value (the two are formatted differently by callers).
    """

    __slots__ = ()


_ATTR_RE = re.compile(
    r"""([\w-]+)                        # attribute key (identifier or dashed)
        \s*=\s*
        (?:
          "([^"]*)"                     # double-quoted string
         |'([^']*)'                     # single-quoted string
         |\{( (?: [^{}] | \{[^{}]*\} )* )\}  # braced expression — the inner
         #                              alternative allows one level of nesting, so
         #                              `items={[{"title": "A"}]}` parses; deeper
         #                              nesting than that is not supported.
        )
      |([\w-]+)                         # bare boolean key
    """,
    re.VERBOSE | re.DOTALL,
)


def parse_jsx_attrs(attrs: str) -> list[tuple[str, Any]]:
    """Parse a JSX-style attribute run into ``(key, value)`` pairs.

    ``value`` is the unquoted content for ``"..."``/``'...'``, an :class:`Expr`
    holding the braced text (without braces) for ``{expr}``, or ``True`` for a
    bare key.
    """
    out: list[tuple[str, Any]] = []
    for m in _ATTR_RE.finditer(attrs):
        if m.group(2) is not None:
            out.append((m.group(1), m.group(2)))
        elif m.group(3) is not None:
            out.append((m.group(1), m.group(3)))
        elif m.group(4) is not None:
            out.append((m.group(1), Expr(m.group(4))))
        else:
            out.append((m.group(5), True))
    return out
