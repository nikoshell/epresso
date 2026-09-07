"""Bundled epresso plugin: MkDocs Material content tabs (``=== "Label"``).

Enable from ``site.toml``::

    plugins = ["epresso_mkdocs_tabs"]

It registers a **render transform** (tabs need to render inner Markdown, so the
core exposes a renderer-aware hook) that expands ``=== "Label"`` blocks into
pure-CSS tabs, and injects the tab styling into every page's ``<head>``.
"""

from __future__ import annotations

import hashlib
import re

from markupsafe import escape

from epresso import markdown as _md
from epresso.plugins import Plugin

_TAB_LABEL = re.compile(r'^=== "([^"]*)"\s*$')

_TABS_CSS = (
    "<style>"
    ".ep-tabs{position:relative;margin:0 0 1rem}"
    ".ep-tabs>input{position:absolute;opacity:0;width:0;height:0}"
    ".ep-tabs>label{display:inline-block;padding:.4rem 1rem;margin:0 2px 0 0;"
    "border:1px solid var(--line,#d0d5dc);border-bottom:0;"
    "border-radius:4px 4px 0 0;background:var(--surface,#fff);"
    "color:var(--muted,#6b7280);cursor:pointer;font-weight:500;font-size:.9em}"
    ".ep-tabs>input:checked+label{color:var(--accent,#a8430e);"
    "border-color:var(--accent,#a8430e);background:var(--bg,#fafafa)}"
    ".ep-tabs>.ep-tabpanel{display:none;border:1px solid var(--line,#d0d5dc);"
    "border-radius:0 4px 4px 4px;padding:1rem;background:var(--surface,#fff)}"
    ".ep-tabs>input:nth-of-type(1):checked~.ep-tabpanel:nth-of-type(1),"
    ".ep-tabs>input:nth-of-type(2):checked~.ep-tabpanel:nth-of-type(2),"
    ".ep-tabs>input:nth-of-type(3):checked~.ep-tabpanel:nth-of-type(3),"
    ".ep-tabs>input:nth-of-type(4):checked~.ep-tabpanel:nth-of-type(4),"
    ".ep-tabs>input:nth-of-type(5):checked~.ep-tabpanel:nth-of-type(5),"
    ".ep-tabs>input:nth-of-type(6):checked~.ep-tabpanel:nth-of-type(6){display:block}"
    "</style>"
)


def _tabs_html(labels, groups, md, depth: int) -> str:
    seed = hashlib.md5("|".join(labels).encode()).hexdigest()[:8]
    head = "".join(
        f'<input type="radio" name="et{seed}" id="et{seed}{i}"{" checked" if i == 0 else ""}>'
        f'<label for="et{seed}{i}">{escape(labels[i])}</label>'
        for i in range(len(labels))
    )
    panels = "".join(
        f'<div class="ep-tabpanel">{_md.render_fragment(md, "\n".join(groups[i]), depth + 1)}</div>'
        for i in range(len(labels))
    )
    return f'<div class="ep-tabs">{head}{panels}</div>'


def _tabs_markdown(md, src: str, depth: int) -> str:
    """Expand ``=== "Label"`` content tabs into raw-HTML tab sets (markdown stays)."""
    if '=== "' not in src:
        return src
    lines = src.split("\n")
    parts: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = _TAB_LABEL.match(lines[i])
        if not m:
            parts.append(lines[i])
            i += 1
            continue
        labels: list[str] = []
        groups: list[list[str]] = []
        while i < n:
            m2 = _TAB_LABEL.match(lines[i])
            if m2:
                labels.append(m2.group(1))
                groups.append([])
                i += 1
                continue
            if groups:
                ln = lines[i]
                if ln.strip() == "" or ln.startswith("    ") or ln.startswith("\t"):
                    ded = ln[4:] if ln.startswith("    ") else (ln[1:] if ln.startswith("\t") else ln)
                    groups[-1].append(ded)
                    i += 1
                    continue
            break
        parts += ["", _tabs_html(labels, groups, md, depth), ""]
    return "\n".join(parts)


def epresso_mkdocs_tabs():
    """Return a ``Plugin`` enabling MkDocs Material content tabs."""

    def before_load(caps):
        caps.add_markdown_render_transform(_tabs_markdown)

    def on_setup(caps):
        caps.inject_head(_TABS_CSS)

    return Plugin(name="epresso_mkdocs_tabs", hooks={"before_load": before_load, "on_setup": on_setup})


# Module-level instance so ``[plugins] = ["epresso_mkdocs_tabs"]`` auto-discovers it.
content_tabs = epresso_mkdocs_tabs()
