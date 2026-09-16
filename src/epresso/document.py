"""EpressoDocument — one parser for the epresso front-matter / ``.ep`` file formats.

The ``--- … ---`` front-matter delimiter and the ``<style>/<script>`` blocks of a
``.ep`` file were previously parsed by bespoke regex in five modules with subtly
diverging rules (``content/loaders``, ``routing``, ``templates``, ``components``,
``fmt``). This module owns the format so a format change or a parser fix lands in
one place:

* the single front-matter delimiter regex,
* the ``.ep`` block extraction (scoped vs global ``<style>``, plus ``<script>``),
* the two front-matter decoders — **YAML** for markdown content (no timestamp
  coercion), raw **Python** for ``.ep`` (callers exec it).

Callers get one :class:`Document` object; ``strip_frontmatter`` and
``split_frontmatter`` serve the narrow needs of the Jinja loader and the
formatter.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from .errors import ContentError

__all__ = [
    "Document",
    "SidecarBlocks",
    "line_at",
    "parse_document",
    "split_frontmatter",
    "strip_frontmatter",
]


def line_at(text: str, pos: int) -> int:
    """1-based line number of ``pos`` in ``text``."""
    return text.count("\n", 0, pos) + 1

# Opening ``--- <spaces>\n`` … closing ``^--- <spaces>\n?`` (line-start). The
# line-start ``^`` (MULTILINE) handles both a non-empty block (``title: x\n---``)
# and an empty one (``---\n---``), while rejecting a mid-line ``---`` inside
# front-matter values (``description: a---b``). ``[\s\S]*?`` spans newlines.
_FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n([\s\S]*?)^---[ \t]*\r?\n?",
    re.DOTALL | re.MULTILINE,
)

# ``<style attrs>…</style>`` and ``<script attrs>…</script>`` blocks (attrs kept).
_STYLE_RE = re.compile(r"<style([^>]*)>([\s\S]*?)</style>", re.IGNORECASE)
_SCRIPT_RE = re.compile(r"<script([^>]*)>([\s\S]*?)</script>", re.IGNORECASE)


def split_frontmatter(source: str) -> tuple[str | None, str]:
    """Return ``(frontmatter_text | None, body)``.

    ``None`` means no ``--- … ---`` block is present (distinct from an empty
    block, which is ``""``). The body is the source with the delimiter stripped.
    """
    m = _FRONTMATTER_RE.match(source)
    if not m:
        return None, source
    return m.group(1), source[m.end():]


def strip_frontmatter(source: str) -> str:
    """Return only the body (used by the Jinja loader, which must never see the
    ``--- … ---`` delimiter)."""
    return split_frontmatter(source)[1]


def _decode_yaml(frontmatter: str) -> dict:
    """YAML-decode markdown front-matter, keeping timestamps as strings.

    SSG front-matter should keep ``date: 2026-01-01`` as the string the author
    wrote; the Pydantic schema decides the real type.
    """
    import yaml

    class _Loader(yaml.SafeLoader):
        pass

    _Loader.add_constructor(
        "tag:yaml.org,2002:timestamp",
        lambda loader, node: loader.construct_scalar(node),  # type: ignore[arg-type]
    )
    try:
        data = yaml.load(frontmatter, Loader=_Loader) or {}
    except Exception as e:  # noqa: BLE001
        raise ContentError(f"invalid YAML front matter: {e}") from e
    if not isinstance(data, dict):
        raise ContentError("front matter must be a mapping")
    return data


def _extract_blocks(body: str) -> tuple[str, str, str, str, SidecarBlocks]:
    """Split a ``.ep`` body into ``(body, scoped_css, scripts, global_css, sidecars)``.

    ``<style is:global>`` / ``<style global>`` blocks are global; other
    ``<style>`` blocks are scoped by default. ``<script>`` blocks are extracted
    and bundled, except ``<script is:inline>`` which stays in the body. All
    extracted style/script blocks are removed from the body.

    ``sidecars`` records the line of every block (grouped by kind) so the
    .ep file-shape rule can cap them without re-parsing the source.
    """
    scoped: list[str] = []
    global_: list[str] = []
    scoped_lines: list[int] = []
    global_lines: list[int] = []
    for m in _STYLE_RE.finditer(body):
        attrs, content = m.group(1), m.group(2)
        line = line_at(body, m.start())
        if re.search(r"\bis:global\b", attrs) or re.search(r"\bglobal\b", attrs):
            global_.append(content)
            global_lines.append(line)
        else:
            scoped.append(content)
            scoped_lines.append(line)
    body = _STYLE_RE.sub("", body)

    scripts: list[str] = []
    # scripts: extract all except <script is:inline> (which stays in the body so
    # it can run in the <head> before first paint — e.g. the theme pre-paint).
    # Counted before the substitution so inline blocks count as sidecars too.
    script_lines = [line_at(body, m.start()) for m in _SCRIPT_RE.finditer(body)]

    def _script_repl(m):
        attrs, content = m.group(1), m.group(2)
        if re.search(r"\bis:inline\b", attrs):
            return m.group(0)  # keep inline in the body
        scripts.append(content)
        return ""

    body = _SCRIPT_RE.sub(_script_repl, body)
    sidecars = SidecarBlocks(tuple(scoped_lines), tuple(global_lines), tuple(script_lines))
    return body, "\n".join(scoped), "\n".join(scripts), "\n".join(global_), sidecars


@dataclass(frozen=True)
class SidecarBlocks:
    """Line numbers of a ``.ep`` file's sidecar blocks, grouped by kind.

    The .ep file-shape rule caps each kind at one (one scoped ``<style>``, one
    ``<style is:global>``, one ``<script>``); recording the lines here keeps that
    check out of the regex business.
    """

    scoped_styles: tuple[int, ...] = ()
    global_styles: tuple[int, ...] = ()
    scripts: tuple[int, ...] = ()

    # NOTE: the line numbers are relative to ``Document.body`` (i.e. after the
    # front-matter); add ``Document.line_offset`` for file-relative lines.


@dataclass
class Document:
    """A parsed epresso source file (a page, component, layout, or content doc).

    ``kind`` selects the front-matter decoder:

    * ``"markdown"`` — YAML-decodes the front-matter into ``data`` (timestamps
      kept as strings).
    * ``"ep"`` — keeps the raw Python front-matter in ``frontmatter`` (callers
      exec it) and extracts ``<style>/<script>`` blocks from ``body``.
    """

    kind: Literal["ep", "markdown"]
    frontmatter: str = ""  # raw front-matter text
    data: dict | None = None  # decoded front-matter (markdown); None for .ep
    body: str = ""  # source body
    scoped_css: str = ""  # concatenated non-global <style> blocks (.ep only)
    scripts: str = ""  # concatenated <script> bodies (.ep only)
    global_css: str = ""  # concatenated global <style> blocks (.ep only)
    sidecars: SidecarBlocks = field(default_factory=SidecarBlocks)  # block lines (.ep only)
    line_offset: int = 0  # lines the front-matter occupies; body line + this = file line


def parse_document(source: str, kind: Literal["ep", "markdown"] = "markdown") -> Document:
    """Parse a source string into a :class:`Document`.

    The delimiter split is shared by both kinds; only the front-matter decoding
    and block extraction differ.
    """
    fm, body = split_frontmatter(source)
    doc = Document(kind=kind, frontmatter=fm or "", body=body)
    # `body` is a suffix of `source`, so the prefix length gives how many lines
    # the front-matter (and its delimiters) occupied — errors report file lines.
    doc.line_offset = source[: len(source) - len(body)].count("\n")
    if kind == "markdown":
        doc.data = _decode_yaml(fm) if fm is not None else {}
    else:
        (doc.body, doc.scoped_css, doc.scripts, doc.global_css, doc.sidecars) = _extract_blocks(body)
    return doc
