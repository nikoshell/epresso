"""Bundled epresso plugin: MkDocs / Material for MkDocs Markdown syntax.

Enable it from ``site.toml`` (the docs theme does)::

    plugins = ["epresso_mkdocs"]

It renders Material content unchanged and emits **Material's HTML classes**, so
``extra_css`` written for Material keeps applying:

- admonitions ``!!! note "Title"`` → ``div.admonition.note`` / ``p.admonition-title``;
  collapsible ``???`` / ``???+`` → ``details.note`` / ``summary``
- content tabs ``=== "Label"`` → ``div.tabbed-set`` / ``.tabbed-labels`` / ``.tabbed-block``
- nested fences inside admonitions, tabs and lists (superfences)
- ``attr_list`` (``{ .class #id key=val }`` on headings, paragraphs, links,
  images, inline code), ``md_in_html`` (``<div markdown>``)
- ``pymdownx.snippets`` (``--8<-- "file.md"``, inside the project only)
- ``def_list``, ``footnotes``, ``abbr``, ``pymdownx.tasklist``,
  ``==mark==``, ``^^ins^^``, ``^sup^``, ``~sub~``, ``++ctrl+alt+del++``
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from markdown_it.token import Token
from markupsafe import escape
from mdit_py_plugins.admon import admon_plugin
from mdit_py_plugins.attrs import attrs_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.subscript import sub_plugin
from mdit_py_plugins.superscript import superscript_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

from epresso import markdown as _md
from epresso.errors import ContentError
from epresso.plugins import Plugin

# ── admonitions, ``???`` as <details> ──────────────────────────────────────


def _admon_classes(token) -> str:
    drop = {"admonition", "is-collapsible", "collapsible-open", "collapsible-closed"}
    return " ".join(c for c in str(token.attrs.get("class", "")).split() if c not in drop)


def _details_plugin(md) -> None:
    """Render ``???`` admonitions as Material's ``<details class="type"><summary>``."""

    def open_(self, tokens, idx, options, env):
        tok = tokens[idx]
        if not tok.markup.startswith("???"):
            return self.renderToken(tokens, idx, options, env)
        level = tok.level
        for t in tokens[idx + 1 :]:  # mark the matching close
            if t.type == "admonition_close" and t.level == level:
                t.meta["details"] = True
                break
        if idx + 1 < len(tokens) and tokens[idx + 1].type == "admonition_title_open":
            tokens[idx + 1].meta["summary"] = True
            tokens[idx + 3].meta["summary"] = True
        is_open = " open" if tok.markup.startswith("???+") else ""
        return f'<details class="{escape(_admon_classes(tok))}"{is_open}>\n'

    def close(self, tokens, idx, options, env):
        return "</details>\n" if tokens[idx].meta.get("details") else "</div>\n"

    def title_open(self, tokens, idx, options, env):
        return "<summary>" if tokens[idx].meta.get("summary") else self.renderToken(tokens, idx, options, env)

    def title_close(self, tokens, idx, options, env):
        return "</summary>\n" if tokens[idx].meta.get("summary") else "</p>\n"

    md.add_render_rule("admonition_open", open_)
    md.add_render_rule("admonition_close", close)
    md.add_render_rule("admonition_title_open", title_open)
    md.add_render_rule("admonition_title_close", title_close)


# ── attr_list on block ends: ``## Title { #id .x }`` / ``para {: .x }`` ────

_ONE_ATTR = r"""(?:[.#][\w-]+|[\w-]+=(?:"[^"]*"|'[^']*'|\S+))"""
_ATTR_TAIL = re.compile(rf"\s*\{{:?\s*({_ONE_ATTR}(?:\s+{_ONE_ATTR})*)\s*\}}\s*$")
_ATTR = re.compile(r"([.#])([\w-]+)|([\w-]+)=(\"[^\"]*\"|'[^']*'|\S+)")


def _apply_attrs(tok, spec: str) -> None:
    classes = [c for c in str(tok.attrs.get("class", "")).split() if c]
    for m in _ATTR.finditer(spec):
        if m.group(1) == ".":
            classes.append(m.group(2))
        elif m.group(1) == "#":
            tok.attrSet("id", m.group(2))
        else:
            tok.attrSet(m.group(3), m.group(4).strip("\"'"))
    if classes:
        tok.attrSet("class", " ".join(classes))


def _block_attrs_plugin(md) -> None:
    def rule(state):
        toks = state.tokens
        for i, tok in enumerate(toks):
            if tok.type != "inline" or i == 0 or toks[i - 1].type not in ("heading_open", "paragraph_open"):
                continue
            m = _ATTR_TAIL.search(tok.content)
            if not m or not tok.children or tok.children[-1].type != "text":
                continue
            last = tok.children[-1]
            tm = _ATTR_TAIL.search(last.content)
            if not tm:
                continue
            last.content = last.content[: tm.start()]
            tok.content = tok.content[: m.start()]
            _apply_attrs(toks[i - 1], m.group(1))

    md.core.ruler.push("epresso_block_attrs", rule)


# ── inline marks: ==mark==, ^^ins^^, ++keys++ ──────────────────────────────

KEY_NAMES = {
    "ctrl": ("control", "Ctrl"),
    "alt": ("alt", "Alt"),
    "shift": ("shift", "Shift"),
    "cmd": ("command", "Cmd"),
    "command": ("command", "Cmd"),
    "meta": ("meta", "Meta"),
    "enter": ("enter", "Enter"),
    "return": ("enter", "Enter"),
    "tab": ("tab", "Tab"),
    "esc": ("escape", "Esc"),
    "escape": ("escape", "Esc"),
    "del": ("delete", "Del"),
    "delete": ("delete", "Del"),
    "backspace": ("backspace", "Backspace"),
    "space": ("space", "Space"),
    "up": ("arrow-up", "Up"),
    "down": ("arrow-down", "Down"),
    "left": ("arrow-left", "Left"),
    "right": ("arrow-right", "Right"),
    "option": ("option", "Option"),
    "fn": ("fn", "Fn"),
}


def _keys_html(spec: str) -> str:
    parts = []
    for raw in spec.split("+"):
        k = raw.strip()
        if k.startswith(("'", '"')) and k.endswith(k[0]):  # ++"custom"++
            parts.append(f"<kbd>{escape(k[1:-1])}</kbd>")
            continue
        cls, label = KEY_NAMES.get(k.lower(), (k.lower(), k.upper() if len(k) == 1 else k.title()))
        parts.append(f'<kbd class="key-{escape(cls)}">{escape(label)}</kbd>')
    return '<span class="keys">' + "<span>+</span>".join(parts) + "</span>"


def _pair_rule(marker: str, tag: str):
    n = len(marker)

    def rule(state, silent: bool) -> bool:
        src, pos = state.src, state.pos
        if not src.startswith(marker, pos):
            return False
        end = src.find(marker, pos + n)
        inner = src[pos + n : end] if end > 0 else ""
        if not inner or inner[0].isspace() or inner[-1].isspace():
            return False
        if not silent:
            tok = state.push("html_inline", "", 0)
            if tag == "keys":
                tok.content = _keys_html(inner)
            else:
                tok.content = f"<{tag}>{state.md.renderInline(inner)}</{tag}>"
        state.pos = end + n
        return True

    return rule


def _marks_plugin(md) -> None:
    md.inline.ruler.before("emphasis", "epresso_mark", _pair_rule("==", "mark"))
    md.inline.ruler.before("emphasis", "epresso_ins", _pair_rule("^^", "ins"))
    md.inline.ruler.before("emphasis", "epresso_keys", _pair_rule("++", "keys"))


# ── abbr: ``*[HTML]: Hyper Text Markup Language`` ──────────────────────────

_ABBR_DEF = re.compile(r"^\*\[([^\]]+)\]:[ \t]*(.*)$", re.M)


def _abbr_plugin(md) -> None:
    def collect(state):
        defs = dict(_ABBR_DEF.findall(state.src))
        if defs:
            state.env["abbr"] = defs
            state.src = _ABBR_DEF.sub("", state.src)

    def apply(state):
        defs = state.env.get("abbr")
        if not defs:
            return
        pat = re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(defs, key=len, reverse=True)) + r")\b")
        for tok in state.tokens:
            if tok.type != "inline" or not tok.children:
                continue
            out = []
            for child in tok.children:
                if child.type != "text" or not pat.search(child.content):
                    out.append(child)
                    continue
                pieces = pat.split(child.content)
                for j, piece in enumerate(pieces):
                    if not piece:
                        continue
                    t = Token("html_inline" if j % 2 else "text", "", 0)
                    t.content = f'<abbr title="{escape(defs[piece])}">{escape(piece)}</abbr>' if j % 2 else piece
                    out.append(t)
            tok.children = out

    md.core.ruler.before("block", "epresso_abbr_defs", collect)
    md.core.ruler.push("epresso_abbr", apply)


# ── content tabs: ``=== "Label"`` → tabbed-set ─────────────────────────────

_TAB_LABEL = re.compile(r'^(?P<ind>[ \t]*)===(?P<sel>\+?) "(?P<label>[^"]*)"\s*$')
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def _tabs_html(labels, groups, md, depth: int, checked: int) -> str:
    """One tab set as a single HTML line (newlines as ``&#10;``), so it stays one
    html block even indented inside an admonition or list item."""
    seed = "t" + hashlib.md5("|".join(labels).encode()).hexdigest()[:8]
    n = len(labels)
    inputs = "".join(
        f'<input{" checked" if i == checked else ""} id="__tabbed_{seed}_{i + 1}" name="__tabbed_{seed}" type="radio">'
        for i in range(n)
    )
    tab_labels = "".join(f'<label for="__tabbed_{seed}_{i + 1}">{escape(labels[i])}</label>' for i in range(n))
    blocks = "".join(
        f'<div class="tabbed-block">{_md.render_fragment(md, chr(10).join(groups[i]), depth + 1)}</div>'
        for i in range(n)
    )
    html = (
        f'<div class="tabbed-set tabbed-alternate" data-tabs="{n}">{inputs}'
        f'<div class="tabbed-labels">{tab_labels}</div><div class="tabbed-content">{blocks}</div></div>'
    )
    return html.replace("\n", "&#10;")


def tabs_transform(md, src: str, depth: int) -> str:
    """Expand ``=== "Label"`` content tabs (at any indent, outside fences) into
    Material's tab-set markup."""
    if '=== "' not in src:
        return src
    lines = src.split("\n")
    parts: list[str] = []
    fence = ""
    i, n = 0, len(lines)
    while i < n:
        fm = _FENCE.match(lines[i])
        if fence or fm:
            if fm and not fence:
                fence = fm.group(1)
            elif fm and fm.group(1).startswith(fence[0]) and len(fm.group(1)) >= len(fence):
                fence = ""
            parts.append(lines[i])
            i += 1
            continue
        first = _TAB_LABEL.match(lines[i])
        if not first:
            parts.append(lines[i])
            i += 1
            continue
        ind = first.group("ind")
        body = ind + "    "
        labels: list[str] = []
        groups: list[list[str]] = []
        checked = 0
        while i < n:
            m = _TAB_LABEL.match(lines[i])
            if m and m.group("ind") == ind:
                if m.group("sel"):
                    checked = len(labels)
                labels.append(m.group("label"))
                groups.append([])
                i += 1
                continue
            ln = lines[i]
            if groups and (ln.strip() == "" or ln.startswith(body)):
                groups[-1].append(ln[len(body) :] if ln.startswith(body) else "")
                i += 1
                continue
            break
        while groups and groups[-1] and groups[-1][-1] == "":  # trailing blanks end the set
            groups[-1].pop()
        if parts and parts[-1].strip():  # one blank line around it: two end an admonition
            parts.append("")
        parts += [ind + _tabs_html(labels, groups, md, depth, checked), ""]
    return "\n".join(parts)


# ── snippets: ``--8<-- "file.md"`` ─────────────────────────────────────────

_SNIP_LINE = re.compile(r'^(?P<ind>[ \t]*)(?P<esc>;)?-{1,}8<-{1,}[ \t]+(["\'])(?P<path>[^"\']+)\3[ \t]*$')
_SNIP_BLOCK = re.compile(r"^[ \t]*-{1,}8<-{1,}[ \t]*$")
_SNIPPET_BASES: list[Path] = []


def _snippet(path: str, seen: tuple[str, ...]) -> str:
    rel = path.split(":", 1)[0] if not re.match(r"^[A-Za-z]:\\", path) else path
    if "://" in rel:
        raise ContentError(f"snippets: remote snippet {rel!r} is not supported")
    for base in _SNIPPET_BASES:
        target = (base / rel).resolve()
        if not target.is_relative_to(base.resolve()):
            raise ContentError(f"snippets: {rel!r} is outside the project")
        if target.is_file():
            if str(target) in seen:
                raise ContentError(f"snippets: {rel!r} includes itself")
            return snippets_transform(target.read_text(encoding="utf-8"), (*seen, str(target)))
    raise ContentError(f"snippets: {rel!r} not found (looked in {', '.join(map(str, _SNIPPET_BASES))})")


def snippets_transform(src: str, seen: tuple[str, ...] = ()) -> str:
    if "8<" not in src:
        return src
    out: list[str] = []
    block: list[str] | None = None
    for line in src.split("\n"):
        if block is not None:
            if _SNIP_BLOCK.match(line):
                for p in block:
                    out.append(_snippet(p, seen))
                block = None
            elif line.strip():
                block.append(line.strip())
            continue
        m = _SNIP_LINE.match(line)
        if m and m.group("esc"):
            out.append(line.replace(";", "", 1))
        elif m:
            ind = m.group("ind")
            out.append("\n".join(ind + ln if ln else ln for ln in _snippet(m.group("path"), seen).split("\n")))
        elif _SNIP_BLOCK.match(line):
            block = []
        else:
            out.append(line)
    return "\n".join(out)


# ── md_in_html: ``<div markdown>`` ─────────────────────────────────────────

_MD_ATTR = re.compile(r"(<[A-Za-z][\w-]*\b[^>]*?)\s+markdown(?:=(?:\"[^\"]*\"|'[^']*'|\w+))?(?=[\s/>])")


def md_in_html_transform(src: str) -> str:
    # ponytail: strips the attribute only; inner Markdown renders when separated
    # from the tags by blank lines, not inline.
    return _MD_ATTR.sub(r"\1", src) if "markdown" in src else src


# ── styles: the tabbed-set needs no JS, only nth-child pairs ─────────────

_TABS_CSS = (
    "<style>"
    + (
        ".tabbed-set{display:flex;flex-wrap:wrap;position:relative;margin:1em 0}"
        ".tabbed-set>input{position:absolute;opacity:0;width:0;height:0}"
        ".tabbed-labels{display:flex;width:100%;overflow:auto;box-shadow:inset 0 -1px var(--line,#d0d5dc)}"
        ".tabbed-labels>label{padding:.5em 1em;cursor:pointer;font-weight:500;font-size:.9em;"
        "color:var(--muted,#6b7280);border-bottom:2px solid transparent;white-space:nowrap}"
        ".tabbed-content{width:100%}.tabbed-block{display:none}"
        + "".join(
            f".tabbed-set>input:nth-child({i}):checked~.tabbed-labels>label:nth-child({i})"
            "{color:var(--accent,#a8430e);border-color:currentColor}"
            f".tabbed-set>input:nth-child({i}):checked~.tabbed-content>.tabbed-block:nth-child({i}){{display:block}}"
            for i in range(1, 21)
        )
    )
    + "</style>"
)


def epresso_mkdocs() -> Plugin:
    """Return the ``Plugin`` that renders MkDocs / Material Markdown syntax."""

    def before_load(caps):
        root = Path(caps.config.root)
        bases = [Path(str(p)) for p in [getattr(caps.config.site, "docs_source", "")] if p]
        _SNIPPET_BASES[:] = [*bases, root]
        caps.add_markdown_source_transform(snippets_transform)
        caps.add_markdown_source_transform(md_in_html_transform)
        caps.add_markdown_render_transform(tabs_transform)
        for fn in (
            admon_plugin,
            _details_plugin,
            deflist_plugin,
            footnote_plugin,
            tasklists_plugin,
            attrs_plugin,
            _block_attrs_plugin,
            _marks_plugin,
            sub_plugin,
            superscript_plugin,
            _abbr_plugin,
        ):
            caps.add_markdown_it_plugin(fn)

    def on_setup(caps):
        caps.inject_head(_TABS_CSS)

    return Plugin(name="epresso_mkdocs", hooks={"before_load": before_load, "on_setup": on_setup})


# Module-level instance so ``plugins = ["epresso_mkdocs"]`` auto-discovers it.
mkdocs = epresso_mkdocs()
