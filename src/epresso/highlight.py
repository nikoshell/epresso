"""Pygments lexer for the ``.ep`` file format.

An ``.ep`` file is::

    ---                      <- Python frontmatter (delimiter)
    from pydantic import BaseModel
    class Props(BaseModel): ...
    ---                      <- delimiter
    <div class="card">…      <- Jinja/HTML body (+ optional <style> / <script>)

We delegate the frontmatter to Python and the body to HTML+Jinja, so ``.ep``
code blocks in the docs are syntax-highlighted. Register it with Pygments so
``get_lexer_by_name("epresso")`` resolves::

    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name
    from epresso.highlight import register

    register()
    highlight(code, get_lexer_by_name("epresso"), HtmlFormatter())
"""

from __future__ import annotations

import re

from pygments.lexer import Lexer
from pygments.lexers import get_lexer_by_name
from pygments.lexers.python import PythonLexer
from pygments.token import Comment

_FM_OPEN = re.compile(r"\A---[ \t]*\r?\n")
_FM_CLOSE = re.compile(r"^---[ \t]*\r?\n", re.MULTILINE)


class EpressoLexer(Lexer):
    """Highlight ``.ep`` files: Python frontmatter + Jinja/HTML body."""

    name = "epresso"
    aliases = ["epresso", "ep"]
    filenames = ["*.ep"]

    def get_tokens_unprocessed(self, text: str):
        body_start = 0
        m = _FM_OPEN.match(text)
        if m:
            close = _FM_CLOSE.search(text, m.end())
            if close:
                fm_py = text[m.end() : close.start()]
                body_start = close.end()
                yield (0, Comment, m.group(0))  # opening `---`
                py = PythonLexer(**self.options)
                for t, tv, val in py.get_tokens_unprocessed(fm_py):
                    yield (m.end() + t, tv, val)
                yield (close.start(), Comment, text[close.start() : close.end()])  # closing `---`
        jinja = get_lexer_by_name("html+jinja", **self.options)
        for t, tv, val in jinja.get_tokens_unprocessed(text[body_start:]):
            yield (body_start + t, tv, val)


def register() -> None:
    """Register :class:`EpressoLexer` with Pygments so ``get_lexer_by_name('epresso')`` works."""
    from pygments.lexers import LEXERS, _lexer_cache

    aliases = tuple(EpressoLexer.aliases)
    LEXERS[aliases] = ("epresso.highlight", "EpressoLexer", "epresso", aliases, ("*.ep",))
    _lexer_cache["EpressoLexer"] = EpressoLexer
