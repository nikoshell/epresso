"""Safe HTML minification — collapses whitespace between tags, strips comments.

Preserves the content of <pre>, <textarea>, <script>, and code blocks, and
minifies the content of inline <style> blocks with :func:`minify_css`.
"""

from __future__ import annotations

import re

_PRESERVE = re.compile(
    r"(<(?:pre|textarea|script|code)(?:\s[^>]*)?>.*?</(?:pre|textarea|script|code)>|\""
    r"[^\"]*\"|'[^']*')",
    re.DOTALL | re.IGNORECASE,
)

_PLACEHOLDER_FMT = "\x00{}\x00"
_PLACEHOLDER_RE = r"\x00(\d+)\x00"


def minify_html(html: str) -> str:
    """Minify HTML, preserving <pre>/<script>/<textarea> and attributes.

    Inline ``<style>`` blocks are minified with :func:`minify_css` so layout
    styles written directly in a layout's <style> tag stay compact.
    """

    # minify inline <style> content (kept separate from _PRESERVE so CSS is
    # tightened rather than just left alone)
    def minify_style(m: re.Match[str]) -> str:
        return f"<style>{minify_css(m.group(1))}</style>"

    html = re.sub(r"<style[^>]*>([\s\S]*?)</style>", minify_style, html, flags=re.IGNORECASE)

    # protect preserved blocks + quoted attribute values
    protected: list[str] = []

    def stash(m: re.Match[str]) -> str:
        protected.append(m.group(0))
        return _PLACEHOLDER_FMT.format(len(protected) - 1)

    html = _PRESERVE.sub(stash, html)

    # remove HTML comments (but not IE conditionals)
    html = re.sub(r"<!--(?!\[if)[\s\S]*?-->", "", html)
    # collapse whitespace between tags
    html = re.sub(r">\s+<", "><", html)
    # collapse runs of spaces/tabs (keep single spaces — they are significant
    # in prose, e.g. "see <a>…" or "</strong> bar", so never strip them)
    html = re.sub(r"[ \t]+", " ", html)
    html = html.strip()

    # restore protected blocks
    def restore(m: re.Match[str]) -> str:
        return protected[int(m.group(1))]

    return re.sub(_PLACEHOLDER_RE, restore, html)


# Remove comments in a single pass that also matches quoted strings, so each is
# consumed as a unit: a `/*` inside a string is not read as a comment, and a quote
# inside a comment is not read as a string. Two stashed passes instead let one
# unbalanced quote in a comment swallow every rule after it.
_CSS_STRING = re.compile(r'"[^"]*"|\'[^\']*\'')
_CSS_COMMENT_OR_STRING = re.compile(r'"[^"]*"|\'[^\']*\'|/\*[\s\S]*?\*/')


def _drop_comment(m: re.Match[str]) -> str:
    text = m.group(0)
    if text.startswith("/*"):
        return text if text.startswith("/*!") else ""  # keep license banners
    return text  # a quoted string


def minify_css(css: str) -> str:
    """Minify CSS: strip comments and collapse whitespace around structural characters.

    ``/*! … */`` banners are kept, since they carry a stylesheet's license, and the
    contents of quoted strings are left byte-for-byte — only whitespace *between*
    declarations is collapsed. Whitespace around ``calc()`` operators (``+ - * /``)
    is preserved, so it is safe for the theme stylesheets.
    """
    css = _CSS_COMMENT_OR_STRING.sub(_drop_comment, css)

    # Stash strings so the collapsing passes cannot touch their contents.
    kept: list[str] = []

    def stash(m: re.Match[str]) -> str:
        kept.append(m.group(0))
        return f"\x01{len(kept) - 1}\x01"

    css = _CSS_STRING.sub(stash, css)
    css = re.sub(r"\s+", " ", css)  # collapse runs of whitespace
    # drop spaces around structural chars (not +/-/*// so calc() stays intact).
    # `:` is handled separately: a space before a pseudo-class (`:hover`, `:not`, …)
    # is a descendant combinator and must be kept, so we never strip whitespace
    # before a `:`. Only the space after a declaration colon is dropped
    # (`color: red` -> `color:red`).
    css = re.sub(r"\s*([{};,>~])\s*", r"\1", css)
    css = re.sub(r":\s+", ":", css)
    css = css.replace("( ", "(").replace(" )", ")")
    css = css.strip()
    return re.sub(r"\x01(\d+)\x01", lambda m: kept[int(m.group(1))], css)
