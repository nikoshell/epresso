"""JSX-style component tags for epresso templates.

Extends Jinja2 so components can be written with HTML-like syntax instead of the
``{% component %}`` tag::

    <Header />
    <FeatureSection layout="three-column" count={n} disabled />
    <Card>…children…</Card>

Implemented as a Jinja2 ``Extension`` whose ``preprocess()`` rewrites component
tags to the existing ``{% component "Name", key=value %}…{% endcomponent %}``
syntax before the template is parsed. Only tags that resolve to a registered
component are converted; every other (HTML) tag passes through untouched, so
``<main>``, ``<div>`` etc. are unaffected.

Attribute syntax (JSX-style):
  * ``key="value"``  → string literal prop
  * ``key='value'``  → string literal prop
  * ``key={expr}``   → Jinja expression prop
  * ``key``          → boolean ``True`` prop

Paired components support children, which may themselves contain components or
arbitrary markup (recursively rewritten).
"""

from __future__ import annotations

import re
from typing import Any

from jinja2.ext import Extension

from .components import _resolve_component
from .jsxattrs import Expr, parse_jsx_attrs

# Protected regions: Jinja constructs ({{ }}, {% %}, {# #}) and <style>/<script>
# blocks. Nothing inside these is rewritten.
_PROTECTED = re.compile(
    r"\{[{%#][\s\S]*?[}%#]\}"
    r"|<(style|script)\b[\s\S]*?</\1>",
    re.IGNORECASE | re.DOTALL,
)

# A quoted-string-aware attribute run, so a ``>`` inside a quoted value does not
# end the tag early.
_ATTRS = r"((?:[^\"'<>]|\"[^\"]*\"|'[^']*')*)"
_OPEN = re.compile(r"<\s*([A-Z][A-Za-z0-9_]*)\b" + _ATTRS + r">", re.DOTALL)


def _is_component(env: Any, name: str) -> bool:
    try:
        return _resolve_component(env, name) is not None
    except Exception:  # noqa: BLE001
        return False


def _parse_attrs(attrs: str) -> list[str]:
    """Parse a tag's attribute run into ``key=value`` tokens for {% component %}."""
    kwargs: list[str] = []
    for key, value in parse_jsx_attrs(attrs):
        if value is True:
            kwargs.append(f"{key}=True")  # bare boolean
        elif isinstance(value, Expr):
            kwargs.append(f"{key}={value.strip()}")  # expression
        else:
            kwargs.append(f"{key}={value!r}")  # quoted string -> Python repr
    return kwargs


def _find_close(text: str, start: int, name: str) -> tuple[int, int] | None:
    """Return (start, end) of the ``</name>`` matching the open tag that ends at ``start``,
    accounting for nested same-name components."""
    open_re = re.compile(r"<\s*" + re.escape(name) + r"\b" + _ATTRS + r">", re.DOTALL)
    close_re = re.compile(r"</\s*" + re.escape(name) + r"\s*>", re.IGNORECASE)
    depth = 1
    i = start
    while i < len(text):
        mo = open_re.search(text, i)
        mc = close_re.search(text, i)
        if mo is None and mc is None:
            return None
        if mo is not None and (mc is None or mo.start() < mc.start()):
            depth += 1
            i = mo.end()
        else:
            assert mc is not None
            depth -= 1
            if depth == 0:
                return mc.start(), mc.end()
            i = mc.end()
    return None


def _emit(name: str, kwargs: list[str], inner: str = "") -> str:
    args = (", " + ", ".join(kwargs)) if kwargs else ""
    return '{% component "' + name + '"' + args + " %}" + inner + "{% endcomponent %}"


def _rewrite(env: Any, source: str) -> str:
    """Rewrite component tags in ``source`` to ``{% component %}`` blocks.

    Jinja constructs and <style>/<script> blocks are preserved verbatim, including
    when they appear *inside* a component's children (so ``<Base>{{ x }}</Base>``
    still rewrites). Nested components are handled recursively.
    """
    out: list[str] = []
    i = 0
    n = len(source)
    while i < n:
        pm = _PROTECTED.search(source, i)  # next protected region (Jinja/style/script)
        m = _OPEN.search(source, i)  # next component open tag
        if m is None:
            if pm is None:
                out.append(source[i:])
                break
            out.append(source[i : pm.start()])
            out.append(pm.group(0))
            i = pm.end()
            continue
        if pm is not None and pm.start() < m.start():
            # protected region comes first -> keep verbatim
            out.append(source[i : pm.start()])
            out.append(pm.group(0))
            i = pm.end()
            continue
        out.append(source[i : m.start()])
        name, attrs = m.group(1), m.group(2)
        tag_end = m.end()
        if not _is_component(env, name):
            out.append(m.group(0))  # plain HTML: keep verbatim
            i = tag_end
            continue
        self_closing = attrs.rstrip().endswith("/")
        attr_source = attrs[: attrs.rfind("/")] if self_closing else attrs
        kwargs = _parse_attrs(attr_source)
        if self_closing:
            out.append(_emit(name, kwargs))
            i = tag_end
        else:
            close = _find_close(source, tag_end, name)
            if close is None:
                out.append(m.group(0))  # unmatched: keep as plain HTML
                i = tag_end
                continue
            cstart, cend = close
            children = _rewrite(env, source[tag_end:cstart])
            out.append(_emit(name, kwargs, children))
            i = cend
    return "".join(out)


class JsxTagsExtension(Extension):
    """Rewrite JSX-style component tags to ``{% component %}`` blocks.

    A preprocess-only extension (no new ``tags``); registered on the environment
    so it runs for every template before parsing.
    """

    tags: set = set()

    def preprocess(self, source: str, name: str | None = None, filename: str | None = None) -> str:
        return _rewrite(self.environment, source)
