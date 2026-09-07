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
section (markup, CSS, JS, frontmatter Python) is preserved verbatim.
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


def format_epresso(text: str) -> str:
    """Normalise a component/page ``.ep`` file to the canonical section order."""
    text = _normalize_eol(text)
    fm_content, body = split_frontmatter(text)
    html, scripts, styles = _extract_blocks(body)

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
    text = _normalize_eol(text)
    out = _strip_trailing_ws(text)
    return out.rstrip("\n") + "\n"


def format_text(text: str) -> str:
    """Format ``.ep`` source, auto-classifying it as component/page or layout."""
    return format_epresso(text) if classify(text) == "component" else format_layout(text)


def format_file(path: Path, write: bool = True, full: bool = False) -> tuple[bool, str]:
    """Compute whether a file would change (and, if ``write``, apply it).

    ``full`` enables deep section-content formatting (frontmatter/HTML/CSS/JS).
    Returns ``(changed, role)``. With ``write=False`` the file is left untouched
    (used by ``fmt --check``).
    """
    text = path.read_text(encoding="utf-8")
    kind = classify(text)
    if full:
        new = format_full(text)
    else:
        new = format_epresso(text) if kind == "component" else format_layout(text)
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


def format_full(text: str) -> str:
    """Deep-format a ``.ep`` file: section contents (frontmatter, HTML, CSS, JS)
    are formatted with the optional formatters, then the structure is
    normalised (role-aware). Falls back to structure-only where a tool is
    missing.
    """
    text = _normalize_eol(text)
    fm_content, body = split_frontmatter(text)
    if fm_content is not None:
        fm_content = _format_python(fm_content)
    body = _deep_format_body(body).lstrip("\n")
    reassembled = (_frontmatter(fm_content) + "\n\n" if fm_content is not None else "") + body
    return format_epresso(reassembled) if classify(text) == "component" else format_layout(reassembled)
