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


def minify_css(css: str) -> str:
    """Minify CSS: strip comments and collapse whitespace around structural characters.

    Whitespace inside strings and around ``calc()`` operators (``+ - * /``) is
    preserved, so it is safe for the theme stylesheets.
    """
    css = re.sub(r"/\*[\s\S]*?\*/", "", css)  # comments
    css = re.sub(r"\s+", " ", css)  # collapse runs of whitespace
    # drop spaces around structural chars (not +/-/*// so calc() stays intact).
    # `:` is handled separately: a space before a pseudo-class (`:hover`, `:not`, …)
    # is a descendant combinator and must be kept, so we never strip whitespace
    # before a `:`. Only the space after a declaration colon is dropped
    # (`color: red` -> `color:red`).
    css = re.sub(r"\s*([{};,>~])\s*", r"\1", css)
    css = re.sub(r":\s+", ":", css)
    css = css.replace("( ", "(").replace(" )", ")")
    return css.strip()
