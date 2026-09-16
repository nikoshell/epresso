"""``epresso fmt`` — normalise ``.ep`` files to the canonical structure.

A ``.ep`` file is a frontmatter block followed by an HTML body that may contain
``<script>`` and ``<style>`` blocks. The canonical layout is::

    --- frontmatter ---
    <HTML body>
    <script>...</script>
    <style>...</style>

with each section separated by a single blank line.

How a file is treated depends on its role (see ``classify``):

* **component / page** — the build parses these via ``document.parse_document``, which
  extracts ``<script>``/``<style>`` out of the body, so their position in the
  file is not semantically meaningful. We reorder them to the canonical order.
* **layout** — a document shell (``Base.ep``) or a ``{% extends %}`` child
  (``Doc.ep``/``Landing.ep``) rendered as a full Jinja template. Its ``<style>``
  lives in ``<head>`` or inside ``{% block head %}`` and is positional, so we
  only apply whitespace hygiene, never reorder.

Only the section structure and whitespace are normalised — the content of each
section (markup, CSS, JS, frontmatter Python) is preserved verbatim, with one
exception: the empty-``else`` idiom ``{% else %}<></>{% endif %}`` collapses to
``{% endif %}`` (identical output, 24 characters shorter).

``epresso fmt --expand`` additionally reflows the HTML body one child per line
(see :func:`_reflow_body`); ``--full`` implies it.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .document import split_frontmatter

# A script or style block, tags + attrs preserved.
_BLOCK_RE = re.compile(
    r"(<script[^>]*>[\s\S]*?</script>|<style[^>]*>[\s\S]*?</style>)",
    re.IGNORECASE,
)


def _normalize_eol(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


# ``{% if c %}X{% else %}<></>{% endif %}`` renders exactly the same as
# ``{% if c %}X{% endif %}`` — the ``<></>`` markers are stripped by
# ``components.unwrap_fragments``. Collapse it so authors don't pay 24 chars for
# an empty branch. Whitespace-control markers (``{%- else -%}``) are left alone:
# their stripping semantics make the rewrite less obviously equivalent.
_EMPTY_ELSE_RE = re.compile(r"\{%\s*else\s*%\}\s*<></>\s*\{%\s*endif\s*%\}")


def _collapse_empty_else(text: str) -> str:
    if "{%" not in text:
        return text
    return _EMPTY_ELSE_RE.sub("{% endif %}", text)


def _strip_trailing_ws(text: str) -> str:
    return "\n".join(line.rstrip(" \t") for line in text.split("\n"))


def classify(text: str) -> str:
    """Return ``"layout"`` if the file is a document shell, else ``"component"``.

    Layouts render as a full Jinja template (``{% extends %}`` or a top-level
    ``<html>/<head>/<body>``), so their ``<style>``/``<script>`` are positional
    and must not be reordered.
    """
    _, body = split_frontmatter(_normalize_eol(text))
    if "{% extends" in body:
        return "layout"
    if re.search(r"<(?:html|head|body)\b", body):
        return "layout"
    return "component"


def _frontmatter(content: str) -> str:
    content = content.strip("\n")
    if not content.strip():
        return "---\n---"
    return f"---\n{content}\n---"


def _extract_blocks(body: str) -> tuple[str, list[str], list[str]]:
    """Split the body into (html, scripts, styles).

    ``<script>``/``<style>`` blocks are extracted (tags preserved) unless they
    share a line with Jinja control flow (``{%``/``{{``), in which case they are
    left in the HTML so their position/conditionals are not disturbed.
    """
    html_parts: list[str] = []
    scripts: list[str] = []
    styles: list[str] = []
    pos = 0
    for m in _BLOCK_RE.finditer(body):
        line_start = body.rfind("\n", 0, m.start()) + 1
        line_end = body.find("\n", m.end())
        line = body[line_start : line_end if line_end != -1 else len(body)]
        # Guard: a block wrapped in Jinja control flow ({% ... %}) shares its
        # line with a "%}" or "{%". Keep those in place so conditionals/loops
        # are not disturbed. ``{{ ... }}`` expressions (e.g. pygments_css) are
        # fine to move — the build renders them in extracted style blocks.
        if "{%" in line or "%}" in line:
            continue  # keep block in place; pos not advanced so it stays in html
        block = m.group(0)
        (scripts if block.lower().lstrip().startswith("<script") else styles).append(block)
        html_parts.append(body[pos : m.start()])
        pos = m.end()
    html_parts.append(body[pos:])
    return "".join(html_parts), scripts, styles


def format_epresso(text: str, expand: bool = False) -> str:
    """Normalise a component/page ``.ep`` file to the canonical section order.

    ``expand`` additionally reflows the HTML body one child per line (see
    :func:`_reflow_body`).
    """
    text = _collapse_empty_else(_normalize_eol(text))
    fm_content, body = split_frontmatter(text)
    html, scripts, styles = _extract_blocks(body)
    if expand:
        html = _reflow_body(html)

    sections: list[str] = []
    if fm_content is not None:
        sections.append(_frontmatter(fm_content))
    if html.strip():
        sections.append(html.strip("\n"))
    sections.extend(s.strip("\n") for s in scripts if s.strip())
    sections.extend(s.strip("\n") for s in styles if s.strip())

    out = _strip_trailing_ws("\n\n".join(sections))
    return out.rstrip("\n") + "\n"


def format_layout(text: str) -> str:
    """Whitespace hygiene for a layout (never reorder script/style)."""
    text = _collapse_empty_else(_normalize_eol(text))
    out = _strip_trailing_ws(text)
    return out.rstrip("\n") + "\n"


def format_text(text: str, expand: bool = False) -> str:
    """Format ``.ep`` source, auto-classifying it as component/page or layout."""
    if classify(text) == "component":
        return format_epresso(text, expand=expand)
    return format_layout(text)


def format_file(path: Path, write: bool = True, full: bool = False, expand: bool = False) -> tuple[bool, str]:
    """Compute whether a file would change (and, if ``write``, apply it).

    ``full`` enables deep section-content formatting (frontmatter/HTML/CSS/JS),
    ``expand`` the one-child-per-line body reflow. Returns ``(changed, role)``.
    With ``write=False`` the file is left untouched (used by ``fmt --check``).
    """
    text = path.read_text(encoding="utf-8")
    kind = classify(text)
    if full:
        new = format_full(text, expand=expand)
    elif kind == "component":
        new = format_epresso(text, expand=expand)
    else:
        new = format_layout(text)
    changed = new != text
    if changed and write:
        path.write_text(new, encoding="utf-8")
    return changed, kind


# ---------------------------------------------------------------------------
# Deep section formatting (frontmatter Python / HTML / CSS / JS)
# ---------------------------------------------------------------------------
# `epresso fmt --full` additionally formats the *contents* of each section by
# reusing dedicated formatters:
#   - frontmatter (Python):  ruff format  (subprocess, stdin)
#   - HTML (body):           djhtml       (subprocess, temp file)
#   - CSS (<style>):         cssbeautifier (library)
#   - JS  (<script>):        jsbeautifier  (library)
#
# These are optional dependencies (``epresso[fmt]``); if any is missing the
# relevant section is left as-is rather than failing the whole run.

_STYLE_RE = re.compile(r"<((?:style|script))([^>]*)>([\s\S]*?)</\1>", re.IGNORECASE)
_JINJA_RE = re.compile(r"(\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\})", re.DOTALL)


def _deep_available() -> bool:
    """Whether the optional deep-formatting tools are installed."""
    try:
        import cssbeautifier  # noqa: F401  # pyright: ignore[reportMissingImports]
        import jsbeautifier  # noqa: F401  # pyright: ignore[reportMissingImports]
    except ImportError:
        return False
    return shutil.which("ruff") is not None and shutil.which("djhtml") is not None


def _format_python(src: str) -> str:
    """Format frontmatter Python with ``ruff format`` (stdin → stdout)."""
    try:
        out = subprocess.run(
            ["ruff", "format", "-"],
            input=src,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        return out.stdout
    except (OSError, subprocess.SubprocessError):
        return src


def _protect_jinja(text: str) -> tuple[str, list[str]]:
    """Replace Jinja tokens with placeholders so generic formatters (css/js)
    don't corrupt them; return ``(protected, tokens)`` for ``_restore_jinja``."""
    parts = _JINJA_RE.split(text)
    tokens: list[str] = []
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # a captured Jinja token
            tokens.append(part)
            out.append(f"__JINJA_{len(tokens) - 1}__")
        else:
            out.append(part)
    return "".join(out), tokens


def _restore_jinja(text: str, tokens: list[str]) -> str:
    for i, tok in enumerate(tokens):
        text = text.replace(f"__JINJA_{i}__", tok)
    return text


def _format_css(css: str) -> str | None:
    if not css.strip():
        return css
    protected, tokens = _protect_jinja(css)
    try:
        import cssbeautifier  # pyright: ignore[reportMissingImports]
    except ImportError:
        return None
    out = cssbeautifier.beautify(protected)
    return _restore_jinja(out, tokens).strip()


def _format_js(js: str) -> str | None:
    if not js.strip():
        return js
    protected, tokens = _protect_jinja(js)
    try:
        import jsbeautifier  # pyright: ignore[reportMissingImports]
    except ImportError:
        return None
    out = jsbeautifier.beautify(protected)
    return _restore_jinja(out, tokens).strip()


def _beautify_style_script(body: str) -> str:
    """Beautify the contents of embedded <style>/<script> blocks in place.

    Blocks are left untouched when the relevant formatter is unavailable (so
    the fallback path doesn't restructure code it can't format).
    """

    def repl(m: re.Match[str]) -> str:
        tag, attrs, content = m.group(1), m.group(2), m.group(3)
        new = _format_css(content) if tag.lower() == "style" else _format_js(content)
        if new is None or new == content.strip():
            return m.group(0)  # leave untouched (no tool / already formatted)
        if not new:
            return f"<{tag}{attrs}>\n</{tag}>"
        return f"<{tag}{attrs}>\n{new}\n</{tag}>"

    return _STYLE_RE.sub(repl, body)


def _djhtml_indent(html: str) -> str:
    """Reindent HTML (Jinja-aware) with ``djhtml`` on a temp file."""
    if not html.strip():
        return html
    tmp = ""
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write(html)
            tmp = f.name
        subprocess.run(["djhtml", tmp], capture_output=True, text=True, timeout=60, check=True)
        return Path(tmp).read_text(encoding="utf-8")
    except (OSError, subprocess.SubprocessError):
        return html
    finally:
        if tmp:
            Path(tmp).unlink(missing_ok=True)


def _deep_format_body(body: str) -> str:
    body = _beautify_style_script(body)
    return _djhtml_indent(body)


def format_full(text: str, expand: bool = False) -> str:
    """Deep-format a ``.ep`` file: section contents (frontmatter, HTML, CSS, JS)
    are formatted with the optional formatters, then the structure is
    normalised (role-aware). Falls back to structure-only where a tool is
    missing. The CLI passes ``expand=True`` for ``--full``.
    """
    text = _normalize_eol(text)
    fm_content, body = split_frontmatter(text)
    if fm_content is not None:
        fm_content = _format_python(fm_content)
    body = _deep_format_body(body).lstrip("\n")
    reassembled = (_frontmatter(fm_content) + "\n\n" if fm_content is not None else "") + body
    if classify(text) == "component":
        return format_epresso(reassembled, expand=expand)
    return format_layout(reassembled)


# ---------------------------------------------------------------------------
# Body reflow (``epresso fmt --expand``)
# ---------------------------------------------------------------------------
# One child per line for elements whose content is *markup only*, Jinja blocks
# spread over three lines, a lone interpolation on its own line. Elements that
# contain literal text (prose, `<pre>`, a `<script>` that survived block
# extraction) are left alone, so paragraph wrapping is never destroyed.
#
# Purely lexical, and guarded: the reflow must not change the sequence of
# non-whitespace characters (``_reflow_body``), so a bug degrades to "file left
# as-is" rather than to a corrupted template.

_INDENT = "    "

# Opaque regions: never reflowed, never re-indented line-by-line.
_RAW_TAGS = r"style|script|pre|textarea"
_VOID_TAGS = frozenset("area base br col embed hr img input link meta param source track wbr".split())

_REFLOW_TOKEN = re.compile(
    r"(?P<comment><!--[\s\S]*?-->|<![^>]*>|\{#.*?#\})"
    r"|(?P<raw>\{%-?\s*raw\s*-?%\}[\s\S]*?\{%-?\s*endraw\s*-?%\})"
    r"|(?P<raw2><(?P<rawtag>" + _RAW_TAGS + r")\b[^>]*>[\s\S]*?</(?P=rawtag)\s*>)"
    r"|(?P<stmt>\{%-?[\s\S]*?-?%\})"
    r"|(?P<expr>\{\{-?[\s\S]*?-?\}\})"
    r"|(?P<frag_open><>)"
    r"|(?P<frag_close></>)"
    r"|(?P<tag></?\s*[A-Za-z][-\w:.]*(?:\"[^\"]*\"|'[^']*'|\{[^}]*\}|[^>\"'{])*>)"
    r"|(?P<text>[^<{]+)"
    r"|(?P<other>[\s\S])",
    re.DOTALL,
)
_TAG_NAME = re.compile(r"^</?\s*([A-Za-z][-\w:.]*)")
_JINJA_NAME = re.compile(r"^\{%-?\s*([A-Za-z_]+)")
_NO_WS = re.compile(r"\s+")


class _Node:
    """A parsed body node. ``kind`` is one of root/el/frag/cond/text/markup."""

    __slots__ = ("kind", "text", "col", "start", "end", "children", "branches", "close")

    def __init__(self, kind: str, text: str = "", col: int = 0, start: int = 0) -> None:
        self.kind = kind
        self.text = text  # leaf text, or the opening tag
        self.col = col  # source column of ``text`` (for tag continuation lines)
        self.start = start  # source offset of the node, for verbatim re-emission
        self.end = start + len(text)
        self.children: list[_Node] = []
        self.branches: list[tuple[str, list[_Node]]] = []  # cond: if/elif/else bodies
        self.close = ""


def _tag_info(text: str) -> tuple[str, bool, bool]:
    """``(name, is_closing, is_self_closing)`` for an HTML tag token."""
    m = _TAG_NAME.match(text)
    name = m.group(1) if m else ""
    return name, text.lstrip().startswith("</"), text.rstrip().endswith("/>")


def _tokens(html: str):
    """Yield ``(kind, text, column, offset)`` tokens covering the whole body."""
    i, n = 0, len(html)
    while i < n:
        m = _REFLOW_TOKEN.match(html, i)
        if m is None:  # pragma: no cover - the `.` fallback always matches
            yield "other", html[i], i - (html.rfind("\n", 0, i) + 1), i
            i += 1
            continue
        col = i - (html.rfind("\n", 0, i) + 1)
        if m.group("comment") is not None:
            kind = "comment"
        elif m.group("raw") is not None or m.group("raw2") is not None:
            kind = "raw"  # opaque: emitted verbatim, never re-flowed or re-indented
        elif m.group("stmt") is not None:
            kind = "stmt"
        elif m.group("expr") is not None:
            kind = "expr"
        elif m.group("frag_open") is not None:
            kind = "frag_open"
        elif m.group("frag_close") is not None:
            kind = "frag_close"
        elif m.group("tag") is not None:
            kind = "tag"
        elif m.group("text") is not None:
            kind = "text"
        else:
            kind = "other"
        yield kind, m.group(0), col, i
        i = m.end()


def _parse_reflow(html: str) -> _Node | None:
    """Build the body tree, or ``None`` when the markup does not nest cleanly."""
    root = _Node("root")
    stack: list[tuple[_Node, list[_Node]]] = [(root, root.children)]
    for kind, text, col, start in _tokens(html):
        container, kids = stack[-1]
        if kind == "text":
            kids.append(_Node("text", text, col, start))
        elif kind in ("comment", "markup", "raw", "expr", "other"):
            kids.append(_Node(kind, text, col, start))
        elif kind == "stmt":
            name = m.group(1) if (m := _JINJA_NAME.match(text)) else ""
            if name in ("if", "for"):
                node = _Node("cond", col=col, start=start)
                node.branches.append((text, []))
                stack.append((node, node.branches[-1][1]))
            elif name in ("elif", "else"):
                if container.kind != "cond":
                    return None
                container.branches.append((text, []))
                stack[-1] = (container, container.branches[-1][1])
            elif name in ("endif", "endfor"):
                if container.kind != "cond":
                    return None
                container.close = text
                container.end = start + len(text)
                stack.pop()
                stack[-1][1].append(container)
            else:
                kids.append(_Node("markup", text, col, start))
        elif kind == "tag":
            name, closing, self_closing = _tag_info(text)
            if closing:
                if container.kind != "el" or _tag_info(container.text)[0] != name:
                    return None
                container.close = text
                container.end = start + len(text)
                stack.pop()
                stack[-1][1].append(container)
            elif self_closing or name in _VOID_TAGS:
                kids.append(_Node("markup", text, col, start))
            else:
                node = _Node("el", text, col, start)
                stack.append((node, node.children))
        elif kind == "frag_open":
            node = _Node("frag", col=col, start=start)
            stack.append((node, node.children))
        else:  # frag_close
            if container.kind != "frag":
                return None
            container.end = start + len(text)
            stack.pop()
            stack[-1][1].append(container)
    if len(stack) != 1:
        return None
    return root


def _collapse_tag(text: str) -> str:
    """One-line tag for inline contexts (attribute whitespace is insignificant)."""
    return _NO_WS.sub(" ", text).strip()


def _inline(node: _Node) -> str:
    """Render a node and everything under it on a single line."""
    if node.kind == "raw":
        return node.text
    if node.kind in ("text", "markup"):
        return _NO_WS.sub(" ", node.text)
    if node.kind == "cond":
        parts = [stmt + "".join(_inline(k) for k in kids) for stmt, kids in node.branches]
        return "".join(parts) + _collapse_tag(node.close)
    if node.kind in ("frag", "root"):
        inner = "".join(_inline(k) for k in node.children)
        return f"<>{inner}</>" if node.kind == "frag" else inner
    inner = "".join(_inline(k) for k in node.children)
    return f"{_collapse_tag(node.text)}{inner}{_collapse_tag(node.close)}"


def _prose(node: _Node, ind: str, html: str) -> str:
    """The node's source, re-based to ``ind`` — prose keeps the author's wrapping.

    An element that contains literal text is never re-rendered: its source span is
    emitted as written, only shifted to the new indentation. Re-flowing it would
    join the paragraph into one long line.
    """
    src = html[node.start : node.end]
    delta = len(ind) - node.col
    out: list[str] = []
    for i, line in enumerate(src.split("\n")):
        if not line.strip():
            out.append("")
            continue
        if i == 0:
            out.append(ind + line.lstrip())
        elif delta > 0:
            out.append(" " * delta + line)
        elif delta < 0:
            out.append(line[min(-delta, len(line) - len(line.lstrip())) :])
        else:
            out.append(line)
    return "\n".join(out)


def _indent_tag(text: str, col: int, level: int) -> list[str]:
    """Indent an opening tag, keeping the author's continuation alignment."""
    ind = _INDENT * level
    lines = text.split("\n")
    out = [ind + lines[0].rstrip()]
    for line in lines[1:]:
        rel = max(0, (len(line) - len(line.lstrip())) - col)
        out.append(" " * (len(ind) + rel) + line.strip())
    return out


def _block_kids(kids: list[_Node]) -> list[_Node]:
    """Children with reporting-whitespace removed (block layout only)."""
    return [k for k in kids if not (k.kind == "text" and not k.text.strip())]


def _has_literal_text(kids: list[_Node]) -> bool:
    """Whether a container holds prose that must not be re-flowed (it would lose
    its line wrapping). ``<pre>``/``<script>``/``{% raw %}`` bodies are opaque
    leaves — they may move onto their own line, but their insides are never
    touched, so they do not force the container to stay on one line.
    """
    return any(k.kind == "text" and k.text.strip() for k in kids)


def _runs(kids: list[_Node]) -> list[list[_Node]]:
    """Group children into runs of nodes that had no whitespace between them.

    ``{% set a %}{% set b %}`` (or ``<a></a><b></b>``) was glued on purpose, so
    it stays on one line; a blank line separates the runs.
    """
    runs: list[list[_Node]] = []
    cur: list[_Node] = []
    after_ws = True
    for kid in kids:
        if kid.kind == "text" and not kid.text.strip():
            after_ws = True
            continue
        if after_ws or not cur:
            if cur:
                runs.append(cur)
            cur = [kid]
        else:
            cur.append(kid)
        after_ws = False
    if cur:
        runs.append(cur)
    return runs


def _emit_children(kids: list[_Node], level: int, lines: list[str], html: str) -> None:
    """Emit a container's children, one run per line.

    Takes the *unfiltered* children: ``_runs`` needs the whitespace-only text
    nodes to tell "glued together" from "separate siblings". A run of more than
    one node is emitted on a single line — the author's missing whitespace is
    significant (``<a>x</a><b>y</b>`` must not gain a space), and staying glued
    is what makes the result a fixpoint.
    """
    for run in _runs(kids):
        if len(run) == 1:
            _emit(run[0], level, lines, html)
        else:
            lines.append(_INDENT * level + "".join(_inline(k) for k in run).strip())


def _emit(node: _Node, level: int, lines: list[str], html: str) -> None:
    ind = _INDENT * level
    if node.kind == "raw":
        lines.append(ind + node.text)  # verbatim — indentation inside may matter
        return
    if node.kind in ("text", "markup"):
        # A tag the author wrapped across lines keeps its wrapping (re-based);
        # collapsing it would produce one 300-character line.
        if "\n" in node.text:
            lines.extend(_indent_tag(node.text, node.col, level))
        else:
            lines.append(ind + node.text.strip())
        return
    if node.kind == "cond":
        for stmt, kids in node.branches:
            lines.append(ind + stmt.strip())
            _emit_children(kids, level + 1, lines, html)
        lines.append(ind + node.close.strip())
        return
    kids = _block_kids(node.children)
    if not kids or _has_literal_text(node.children):
        lines.append(_prose(node, ind, html))  # prose — never re-flowed
        return
    if node.kind == "root":
        _emit_children(node.children, level, lines, html)
        return
    if node.kind == "frag":
        lines.append(ind + "<>")
        _emit_children(node.children, level + 1, lines, html)
        lines.append(ind + "</>")
        return
    lines.extend(_indent_tag(node.text, node.col, level))
    _emit_children(node.children, level + 1, lines, html)
    lines.append(ind + _collapse_tag(node.close))


def _reflow(html: str) -> str | None:
    root = _parse_reflow(html)
    if root is None:
        return None
    lines: list[str] = []
    _emit_children(root.children, 0, lines, html)
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _reflow_body(html: str) -> str:
    """Reflow an HTML body to one child per line, or return it unchanged.

    The rewrite only ever moves whitespace: if the result no longer contains the
    same non-whitespace characters in the same order, the input is returned
    untouched rather than risking a corrupted template.
    """
    try:
        new = _reflow(html)
    except Exception:  # noqa: BLE001 - a formatter must never break a build
        return html
    if new is None or _NO_WS.sub("", new) != _NO_WS.sub("", html):
        return html
    return new + "\n"
