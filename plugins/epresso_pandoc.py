"""Bundled epresso plugin: Pandoc fenced-code and image attributes.

Enable it from a project's ``site.toml``::

    plugins = ["epresso_pandoc"]

It registers two markdown extensions via the plugin API: a **source transform**
that normalizes Pandoc ``{...}`` fenced-code attributes (so ``{.python .no-copy}``
sets the language and classes), and an **html post-processor** that consumes
Pandoc image attributes (``![..](..){style="width: 70%"}``) into the ``<img>``.
"""

from __future__ import annotations

import re

from epresso.plugins import Plugin

_FENCE_OPEN = re.compile(r"^(?P<ind>[ \t]{0,3})(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


def _pandoc_fence_info(info: str) -> str:
    """Normalize a Pandoc-style fenced-code attribute group to markdown-it form."""
    info = info.strip()
    b = info.find("{")
    if b < 0:
        return info
    e = info.find("}", b)
    if e < 0:
        return info
    head, group, tail = info[:b].strip(), info[b + 1 : e], info[e + 1 :].strip()
    toks = [t for t in group.split() if t]
    classes = [t[1:] for t in toks if t.startswith(".")]
    keyvals = [t for t in toks if not t.startswith(".")]
    lang = head
    if not lang and classes:
        lang = classes.pop(0)
    parts: list[str] = [lang] if lang else []
    parts += ["." + c for c in classes]
    for k in keyvals:
        parts.append(f'{k.split("=", 1)[0]}="{k.split("=", 1)[1]}"' if "=" in k else k)
    if tail:
        parts.append(tail)
    return " ".join(parts)


def _normalize_fence_attrs(src: str) -> str:
    """Rewrite Pandoc ``{...}`` fenced-code attributes across the source lines."""
    lines = src.split("\n")
    for i, line in enumerate(lines):
        m = _FENCE_OPEN.match(line)
        if m and "{" in m.group("info"):
            lines[i] = m.group("ind") + m.group("fence") + " " + _pandoc_fence_info(m.group("info"))
    return "\n".join(lines)


_IMG_ATTRS = re.compile(r"(<img\b[^>]*?/?>)\s*\{([^{}]*)\}")


def _rewrite_image_attrs(html: str) -> str:
    """Consume Pandoc image attributes (``![..](..){style=".."}``) into the <img>."""
    import html as _h

    def _repl(m):
        img, attr = m.group(1), m.group(2)
        attr = _h.unescape(attr)  # markdown-it escapes quotes inside the braces
        style = ""
        sm = re.search(r'style\s*=\s*"([^"]*)"', attr)
        if sm:
            style = sm.group(1)
        for key in ("width", "height"):
            kv = re.search(key + r'\s*=\s*"?([^"\s}]+)"?', attr)
            if kv and kv.group(1) not in style:
                style = ((style + "; ") if style else "") + key + ": " + kv.group(1)
        extra = (' style="' + _h.escape(style) + '"') if style else ""
        return (img[:-2] + extra + "/>") if img.endswith("/>") else (img[:-1] + extra + ">")

    return _IMG_ATTRS.sub(_repl, html)


def epresso_pandoc():
    """Return a ``Plugin`` enabling Pandoc fenced-code + image attributes."""

    def before_load(caps):
        caps.add_markdown_source_transform(_normalize_fence_attrs)
        caps.add_html_postprocess(_rewrite_image_attrs)

    return Plugin(name="epresso_pandoc", hooks={"before_load": before_load})


# Module-level instance so ``[plugins] = ["epresso_pandoc"]`` auto-discovers it.
pandoc = epresso_pandoc()
