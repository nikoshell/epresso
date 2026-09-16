"""PIN CURRENT BEHAVIOR (Phase 0 guard for the author-scope change).

These document how epresso scopes *slotted content today*: markup a caller writes
and passes into a scoped child is stamped with the **child's** scope (the first
scoped renderer to see it), NOT the caller/author's. This is the "consumer owns
the slotted subtree" model that the author-scope change (Phase 1) inverts.

After the renderer change (Phase 1) the "author owns its passed content" tests
here flip: the <em> should carry Caller's scope. They are updated then — they run
green against the *current* engine as a baseline.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from epresso.site import Site


def _render(files: dict[str, str]) -> str:
    d = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    site = Site.load(d)
    site.build()
    return (site.config.dir_output() / "index.html").read_text()


def _scope_attrs(tag: str) -> list[str]:
    return re.findall(r"data-epresso-[a-f0-9]+", tag)


def _opening(html: str, needle: str) -> str:
    return re.search(needle, html).group(0)


# ---- NEW behavior: the author owns caller-passed content -------------------


def test_caller_passed_content_is_scoped_to_the_author_not_the_child():
    """A <em> written by Caller and passed into Child now carries **Caller**'s
    scope, so Caller can style it with its own scoped CSS (author scoping)."""
    html = _render(
        {
            "components/Child.ep": "<div class='c'>{{ content }}</div>\n<style>.c{color:red}</style>",
            "components/Caller.ep": (
                "<section class='s'><Child><em class='k'>hi</em></Child></section>\n"
                "<style>.s{color:blue}.k{color:green}</style>"
            ),
            "pages/index.ep": "---\n---\n<Caller />",
        }
    )
    em = _opening(html, r"<em class='k'[^>]*>")
    child = _opening(html, r"<div class='c'[^>]*>")
    sec = _opening(html, r"<section class='s'[^>]*>")

    em_scope = _scope_attrs(em)
    child_scope = _scope_attrs(child)
    sec_scope = _scope_attrs(sec)

    # the caller-authored <em> now carries the *caller's* scope (1 attr), not the child's
    assert len(em_scope) == 1
    assert em_scope == sec_scope      # Caller (the author) owns it
    assert em_scope != child_scope    # NOT the child's scope
