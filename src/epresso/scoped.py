"""Scoped CSS — the transform behind the CONTEXT.md **Scoped CSS** concept.

Two pure transforms:

* :func:`scope_css` — rewrite a component's scoped CSS so each selector carries
  ``data-epresso-<hash>``. Parsed with **tinycss2** (a real CSS
  parser), so ``:global(...)`` is stripped, ``@keyframes`` is left untouched,
  and scoping recurses into rule-containing at-rules.
* :func:`inject_scope_attr` — add ``data-epresso-<hash>`` to element opening tags.
"""

from __future__ import annotations

import re

import tinycss2
from tinycss2 import serialize as _serialize
from tinycss2.ast import (
    AtRule,
    FunctionBlock,
    IdentToken,
    LiteralToken,
    QualifiedRule,
    SquareBracketsBlock,
    WhitespaceToken,
)

__all__ = ["scope_css", "inject_scope_attr"]

# At-rules that contain nested style rules which must also be scoped.
_RULE_AT_RULES = {"media", "supports", "layer", "container", "scope", "document"}


def _is_combinator(tok) -> bool:
    return isinstance(tok, WhitespaceToken) or (isinstance(tok, LiteralToken) and tok.value in ">+~")


def _is_comma(tok) -> bool:
    return isinstance(tok, LiteralToken) and tok.value == ","


def _scope_marker(scope_hash: str, strategy: str, line: int, column: int):
    block = SquareBracketsBlock(line, column, [IdentToken(line, column, f"data-epresso-{scope_hash}")])
    if strategy == "where":
        return [LiteralToken(line, column, ":"), FunctionBlock(line, column, "where", [block])]  # :where([…])
    return [block]  # attribute strategy: [data-epresso-…]


def _scope_compound(compound, scope_hash: str, strategy: str):
    """Rewrite one compound selector: strip ``:global(...)`` or append the scope."""
    if compound and isinstance(compound[0], LiteralToken) and compound[0].value == ":":
        # A bare pseudo compound (`:hover`, `::before`, `:global(...)`) has no
        # element to scope. `:global(...)` is stripped to its inner selector.
        if len(compound) >= 2 and isinstance(compound[1], FunctionBlock) and compound[1].name == "global":
            return compound[1].arguments
        return compound
    # Insert the scope before the first pseudo (`:hover`/`::before`), else at the end.
    idx = next((i for i, t in enumerate(compound) if isinstance(t, LiteralToken) and t.value == ":"), len(compound))
    ref = compound[idx] if idx < len(compound) else compound[-1]
    marker = _scope_marker(scope_hash, strategy, ref.source_line, ref.source_column)
    return compound[:idx] + marker + compound[idx:]


def _scope_selector(prelude, scope_hash: str, strategy: str):
    """Rewrite a selector list: scope each compound selector, preserve combinators."""
    out = []
    current = []

    def flush():
        nonlocal current
        if current:
            out.extend(_scope_compound(current, scope_hash, strategy))
            current = []

    for tok in prelude:
        if _is_combinator(tok) or _is_comma(tok):
            flush()
            out.append(tok)
        else:
            current.append(tok)
    flush()
    return out


def _process_rules(rules, scope_hash: str, strategy: str):
    for rule in rules:
        if isinstance(rule, QualifiedRule):
            rule.prelude = _scope_selector(rule.prelude, scope_hash, strategy)
        elif isinstance(rule, AtRule) and rule.at_keyword.lower() in _RULE_AT_RULES and rule.content is not None:
            inner = tinycss2.parse_rule_list(rule.content)
            _process_rules(inner, scope_hash, strategy)
            rule.content = tinycss2.parse_component_value_list(_serialize(inner))
    return rules


def scope_css(css: str, scope_hash: str, strategy: str = "attribute") -> str:
    """Rewrite scoped CSS so each selector carries ``data-epresso-<hash>``.

    Parsed with tinycss2 (a real CSS parser), so:

    * ``:global(...)`` selectors are stripped to their inner selector, unscoped;
    * ``@keyframes`` selectors are left untouched;
    * scoping recurses into rule-containing at-rules (``@media``, ``@supports`` …).

    ``strategy`` attaches the scope as ``"attribute"`` (``[data-epresso-<hash>]``)
    or ``"where"`` (``:where([data-epresso-<hash>])`` — zero specificity).
    """
    rules = tinycss2.parse_stylesheet(css, skip_whitespace=False, skip_comments=False)
    return _serialize(_process_rules(rules, scope_hash, strategy))


def inject_scope_attr(html: str, scope_hash: str) -> str:
    """Add ``data-epresso-<hash>`` to element opening tags in ``html``.

    Elements that already carry a ``data-epresso-*`` attribute (a nested child
    component's output) are left untouched, so each element keeps the scope of the
    innermost component that scoped it — a parent's scope does not cascade into
    child components (isolated). Comments, closing tags, doctypes
    and <style>/<script> are skipped.
    """
    attr = f" data-epresso-{scope_hash}"
    pattern = re.compile(r"<[^>]+>")

    def repl(m: re.Match[str]) -> str:
        tag = m.group(0)
        if tag.startswith(("<!--", "<!", "</", "<style", "<script")):
            return tag
        if "data-epresso-" in tag:
            return tag  # already scoped (child component) — keep its own scope
        inner = tag[1:-1].strip()
        if inner.endswith("/"):
            return f"<{inner[:-1].rstrip()}{attr}/>"
        return f"<{inner}{attr}>"

    return pattern.sub(repl, html)
