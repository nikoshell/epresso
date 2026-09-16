"""Document which elements carry `data-epresso-*` — the scoping model.

A component is scoped only when it contains a scoped `<style>`; its elements are
then stamped with `data-epresso-<hash>`. A component with no scoped CSS (or only
`<style is:global>`) is unscoped. Nested scoped components keep each element at
its innermost scope: a child element carries only the child's id, and a parent's
pass does not restamp child elements — parent scoped CSS
does not cascade into children).
"""

from pathlib import Path

from epresso.site import Site


def _render(files):
    import tempfile

    d = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    site = Site.load(d)
    site.build()
    return (site.config.dir_output() / "index.html").read_text()


def _scope_attrs(tag: str) -> list[str]:
    import re

    return re.findall(r"data-epresso-[a-f0-9]+", tag)


def test_component_without_scoped_style_is_unscoped():
    # A component with no scoped CSS (markup only) renders without data-epresso-*.
    html = _render(
        {
            "components/Plain.ep": "<p>hi</p>",
            "pages/index.ep": "---\n---\n<Plain />",
        }
    )
    assert "data-epresso-" not in html


def test_component_with_global_style_is_unscoped():
    # <style is:global> does not opt the component into scoping.
    html = _render(
        {
            "components/Plain.ep": "<p>hi</p>\n<style is:global>.x{color:red}</style>",
            "pages/index.ep": "---\n---\n<Plain />",
        }
    )
    assert "data-epresso-" not in html


def test_full_document_global_style_lands_in_head():
    # A slot-based layout that emits a full <html><head> document, with a
    # <style is:global> block, gets its base CSS injected into the <head> — not
    # dumped before the doctype (which would be invalid HTML).
    html = _render(
        {
            "layouts/Base.ep": (
                "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
                "<title>{{ props.title or 'site' }}</title></head>"
                "<body><slot /></body></html>"
                "<style is:global>:root{--a:#000}.x{color:red}</style>"
            ),
            "pages/index.md": "---\nlayout: Base\ntitle: hi\n---\n\n<p>body</p>",
        }
    )
    assert html.startswith("<!doctype html>")  # style did not land before the doctype
    assert html.count("<style>") == 1
    assert html.find(":root") > html.find("<head>")
    assert html.find(":root") < html.find("</head>")


def test_component_with_scoped_style_marks_its_elements():
    html = _render(
        {
            "components/Scoped.ep": "<div class='x'>hi</div>\n<style>.x{color:red}</style>",
            "pages/index.ep": "---\n---\n<Scoped />",
        }
    )
    assert "data-epresso-" in html
    m = __import__("re").search(r"<div[^>]*>", html)
    assert m and _scope_attrs(m.group(0))


def test_nested_scoped_component_keeps_own_scope_only():
    # A child element inside a scoped parent carries only the child's scope —
    # the parent's pass skips already-scoped output, so the
    # element has a single data-epresso-* and parent CSS can't leak into it.
    html = _render(
        {
            "components/Child.ep": "<button class='c'>{{ content }}</button>\n<style>.c{color:red}</style>",
            "components/Parent.ep": "<div class='p'><Child>hi</Child></div>\n<style>.p{color:blue}</style>",
            "pages/index.ep": "---\n---\n<Parent />",
        }
    )
    m = __import__("re").search(r"<button[^>]*>", html)
    assert m
    attrs = _scope_attrs(m.group(0))
    assert len(attrs) == 1  # only the child's own scope, not the parent's

    # the parent's own element still carries the parent scope
    pm = __import__("re").search(r"<div class='p'[^>]*>", html)
    assert pm and _scope_attrs(pm.group(0))


def test_sibling_scoped_components_get_distinct_scopes():
    html = _render(
        {
            "components/A.ep": "<span class='a'>A</span>\n<style>.a{color:red}</style>",
            "components/B.ep": "<span class='b'>B</span>\n<style>.b{color:blue}</style>",
            "pages/index.ep": "---\n---\n<Fragment><A /><B /></Fragment>",
        }
    )
    a = __import__("re").search(r"<span class='a'[^>]*>", html).group(0)
    b = __import__("re").search(r"<span class='b'[^>]*>", html).group(0)
    assert _scope_attrs(a) != _scope_attrs(b)
