"""Tests for the ``epresso fmt`` formatter (``src/epresso/fmt.py``)."""

from __future__ import annotations

import shutil

import pytest

from epresso.fmt import (
    classify,
    format_epresso,
    format_full,
    format_layout,
    format_text,
)


def test_format_component_reorders_sections():
    src = (
        "---\n"
        "from pydantic import BaseModel\n"
        "---\n"
        "\n"
        "<style>.a { color: red; }</style>\n"
        "<p>hello</p>\n"
        "<script>console.log(1);</script>\n"
    )
    out = format_epresso(src)
    assert out == (
        "---\n"
        "from pydantic import BaseModel\n"
        "---\n"
        "\n"
        "<p>hello</p>\n"
        "\n"
        "<script>console.log(1);</script>\n"
        "\n"
        "<style>.a { color: red; }</style>\n"
    )


def test_is_global_style_with_jinja_expression_grouped_with_styles():
    """A <style> containing {{ ... }} (e.g. pygments_css) is still a style block
    and should be grouped in the styles section, not left in the HTML body."""
    src = "<p>body</p>\n<style>{{ pygments_css('x') }}</style>\n<script>run();</script>\n"
    out = format_epresso(src)
    # body first, then script, then style
    assert out.index("<p>body</p>") < out.index("<script>run();</script>")
    assert out.index("<script>run();</script>") < out.index("<style>{{ pygments_css('x') }}</style>")


def test_conditional_script_stays_in_place():
    """A <script> sharing a line with Jinja control flow ({% %}) is not moved."""
    src = "{% if cond %}<script>run()</script>{% endif %}\n<p>body</p>\n"
    out = format_epresso(src)
    assert "{% if cond %}<script>run()</script>{% endif %}" in out
    assert out.count("<script>") == 1


def test_format_collapses_empty_else():
    """The empty-branch idiom collapses: ``{% else %}<></>{% endif %}`` -> ``{% endif %}``
    (identical output, the ``<></>`` markers are stripped at render time anyway)."""
    src = "{% if x %}<a>y</a>{% else %}<></>{% endif %}\n"
    want = "{% if x %}<a>y</a>{% endif %}\n"
    assert format_epresso(src) == want
    assert format_text(src) == want
    assert format_layout(src) == want
    assert format_full(src) == want
    # multi-line / spaced variants too
    assert format_epresso("{% if x %}<a>y</a>{%else%}<></>\n{% endif %}\n") == want


def test_collapsed_else_renders_identically():
    """The rewrite is output-preserving: ``<></>`` is stripped and an empty else
    emits nothing, so both forms render the same HTML for either branch."""
    from jinja2 import Environment

    from epresso.components import unwrap_fragments

    env = Environment()
    old = env.from_string("{% if x %}<a>y</a>{% else %}<></>{% endif %}")
    new = env.from_string("{% if x %}<a>y</a>{% endif %}")
    for x in (True, False):
        assert unwrap_fragments(old.render(x=x)) == unwrap_fragments(new.render(x=x))


def test_format_leaves_whitespace_control_else_alone():
    """A ``{%- else -%}`` has stripping semantics; don't rewrite it."""
    src = "{% if x %}<a>y</a>{%- else -%}<></>{% endif %}\n"
    assert "<></>" in format_epresso(src)


def test_extends_layout_not_reordered():
    src = (
        '{% extends "Base.ep" %}\n'
        "{% block head %}\n"
        "<style>.doc { color: red; }</style>\n"
        "{% endblock %}\n"
        "{% block body %}hi{% endblock %}\n"
    )
    assert classify(src) == "layout"
    out = format_layout(src)
    # style stays inside {% block head %}
    assert "{% block head %}\n<style>.doc { color: red; }</style>" in out


def test_document_shell_classified_layout():
    src = "<!doctype html>\n<html><head><style>body {}</style></head><body>x</body></html>\n"
    assert classify(src) == "layout"
    # format_text uses layout path -> style stays in <head>
    out = format_text(src)
    assert "<head><style>body {}</style></head>" in out


def test_classify_component_default():
    assert classify("<p>hi</p>\n<style>.a {}</style>\n") == "component"


def test_idempotent():
    src = "---\nx: 1\n---\n\n<p>body</p>\n<script>run();</script>\n<style>.a {}</style>\n"
    once = format_epresso(src)
    assert format_epresso(once) == once


def test_trailing_whitespace_and_newline():
    src = "<p>hi</p>   \n<style>.a {}</style>   \n"
    out = format_epresso(src)
    assert "</p>   " not in out
    assert out.endswith("\n")
    assert "   \n" not in out


def test_mid_line_whitespace_preserved():
    """Whitespace inside a line is meaningful and must be preserved."""
    src = "<p>a   b</p>\n"
    out = format_epresso(src)
    assert "a   b" in out


def test_empty_frontmatter_normalized():
    src = "---\n\n---\n<p>hi</p>\n"
    out = format_epresso(src)
    assert out.startswith("---\n---\n")


def test_layout_hides_trailing_whitespace_only():
    src = '{% extends "Base.ep" %}\n{% block body %}x{% endblock %}   \n'
    out = format_layout(src)
    assert "x{% endblock %}   " not in out
    assert out.endswith("\n")


def test_format_full_structure_fallback():
    """format_full is structure-safe and idempotent even when optional deps are
    missing (it falls back to structure-only normalisation)."""
    src = "<p>hi</p>\n<script>run();</script>\n<style>.a{}</style>\n"
    out = format_full(src)
    assert out.index("<p>hi</p>") < out.index("<script>run();</script>")
    assert format_full(out) == out


def test_format_full_preserves_jinja():
    src = "{% if cond %}<script>run()</script>{% endif %}\n<p>hi</p>\n"
    out = format_full(src)
    assert "{% if cond %}<script>run()</script>{% endif %}" in out


def test_format_full_deep_when_tools_present():
    """With the optional [fmt] tools installed, frontmatter/CSS/JS are formatted."""
    pytest.importorskip("cssbeautifier")
    pytest.importorskip("jsbeautifier")
    if shutil.which("ruff") is None or shutil.which("djhtml") is None:
        pytest.skip("ruff/djhtml not on PATH")
    from epresso.fmt import format_full

    src = (
        "---\n"
        "class P:\n"
        "    x:int=1\n"
        "---\n"
        "<p>hi</p>\n"
        "<style>.a{color:red;margin:0}</style>\n"
        "<script>function f(){var a=1;if(a){return a}}</script>\n"
    )
    out = format_full(src)
    # frontmatter formatted by ruff
    assert "    x: int = 1" in out
    # css expanded onto multiple lines
    assert ".a {\n" in out
    # js expanded
    assert "function f() {\n" in out


def test_format_full_idempotent_layout():
    """format_full must be idempotent for layout-style files (regression: a
    leading blank line in the body accumulated on each pass)."""
    from epresso.fmt import format_full

    src = (
        "---\nclass P:\n    x:int=1\n---\n"
        "<!doctype html><html><head><style>.a{color:red}</style></head>"
        "<body>{{ content }}</body></html>"
    )
    once = format_full(src)
    assert format_full(once) == once


# ── --expand: one child per line ──────────────────────────────────────────

_EXPANDED_ALERT_BODY = """\
<div role="{{ tone.role }}"
     class="{{ cn(BASE, tone.rule, props.class_name) }}">
    {% if props.icon %}
        <Icon name={tone.icon} class_name={cn('mt-0.5', tone.accent)} />
    {% endif %}
    <div class="flex min-w-0 flex-col gap-1">
        {% if label %}
            <span class="mono-label {{ tone.accent }}">
                {{ label }}
            </span>
        {% endif %}
        {% if props.title %}
            <p class="font-semibold text-foreground">
                {{ props.title }}
            </p>
        {% endif %}
        {% if props.description %}
            <p class="text-muted-foreground">
                {{ props.description }}
            </p>
        {% endif %}
        {{ content }}
    </div>
</div>
"""


_ALERT_BODY = (
    '<div role="{{ tone.role }}"\n'
    '     class="{{ cn(BASE, tone.rule, props.class_name) }}">\n'
    "    {% if props.icon %}<Icon name={tone.icon} class_name={cn('mt-0.5', tone.accent)} />{% endif %}\n"
    '    <div class="flex min-w-0 flex-col gap-1">\n'
    '        {% if label %}<span class="mono-label {{ tone.accent }}">{{ label }}</span>{% endif %}\n'
    '        {% if props.title %}<p class="font-semibold text-foreground">{{ props.title }}</p>{% endif %}\n'
    '        {% if props.description %}<p class="text-muted-foreground">{{ props.description }}</p>{% endif %}\n'
    "        {{ content }}\n"
    "    </div>\n"
    "</div>\n"
)


def test_expand_markup_only_element_gets_one_child_per_line():
    assert format_epresso(_ALERT_BODY, expand=True) == _EXPANDED_ALERT_BODY


def test_expand_keeps_prose_inline():
    """Text children mean the element is left alone: reflowing prose would move
    the author's line breaks into the rendered page."""
    src = "<p>Hello <b>world</b> — and more text that keeps wrapping.</p>\n"
    assert format_epresso(src, expand=True) == src
    nested = "<div class='a'><p>Some <em>inline</em> prose</p>\n<p>More</p></div>\n"
    out = format_epresso(nested, expand=True)
    assert "<p>Some <em>inline</em> prose</p>" in out  # untouched
    assert "<p>More</p>" in out


def test_expand_leaves_opaque_bodies_verbatim():
    """<pre>/<script>/<textarea> interiors may sit on their own line, but their
    whitespace is significant and must not be touched."""
    src = '<div class="a">\n<pre>if (a < b) {\n  x()\n}</pre>\n</div>\n'
    out = format_epresso(src, expand=True)
    assert "if (a < b) {\n  x()\n}" in out
    js = '<div class="a">\n<script>if (a) {\n  b()\n}</script>\n</div>\n'
    out = format_epresso(js, expand=True)
    assert "if (a) {\n  b()\n}" in out


def test_expand_glues_what_the_author_glued():
    """Adjacent statements with no whitespace between them stay on one line."""
    src = "{% set a = 1 %}{% set b = 2 %}\n<div>x</div>\n"
    assert format_epresso(src, expand=True) == "{% set a = 1 %}{% set b = 2 %}\n<div>x</div>\n"


def test_expand_adds_no_blank_lines():
    src = '<div class="a">\n    <span>x</span>\n    <span>y</span>\n</div>\n'
    out = format_epresso(src, expand=True)
    assert "\n\n" not in out


def test_expand_does_not_split_html_comments():
    src = "<div class='a'>\n<!-- one root: the group -->\n<span>{{ x }}</span>\n</div>\n"
    out = format_epresso(src, expand=True)
    assert "<!-- one root: the group -->" in out


def test_expand_returns_unparseable_bodies_unchanged():
    """A formatter must never corrupt a template: unbalanced markup is left as-is."""
    src = "<div class='a'>\n<span>x</span>\n</div></p>\n"
    assert format_epresso(src, expand=True) == format_epresso(src)


def test_expand_is_idempotent_and_whitespace_only():
    """Every real theme component reflows to a fixpoint without changing a single
    non-whitespace character."""
    import re
    from pathlib import Path

    theme = Path(__file__).resolve().parents[2] / "themes"
    strip = lambda s: re.sub(r"\s+", "", s)  # noqa: E731
    checked = 0
    for path in sorted(theme.rglob("*.ep")):
        src = path.read_text(encoding="utf-8")
        if classify(src) == "layout":
            continue
        out = format_epresso(src, expand=True)
        assert strip(out) == strip(src), f"content changed for {path}"
        assert format_epresso(out, expand=True) == out, f"not idempotent: {path}"
        checked += 1
    assert checked > 10


def test_expand_reaches_format_file_and_full(tmp_path):
    from epresso.fmt import format_file

    src = "---\n---\n<div class='a'>\n<span>{{ x }}</span>\n</div>\n"
    path = tmp_path / "A.ep"
    path.write_text(src, encoding="utf-8")
    changed, kind = format_file(path, expand=True)
    assert changed and kind == "component"
    assert "<span>\n        {{ x }}\n    </span>" in path.read_text(encoding="utf-8")


def test_expand_treats_capitalised_components_as_containers():
    """`<Base>`/`<Link>`/`<Source>` are components, not the HTML void elements
    `<base>`/`<link>`/`<source>` — matching void tags case-insensitively makes the
    parser lose the element and silently skip the whole file."""
    src = "<Base title={META['title']}>\n<div class='a'>\n<span>x</span>\n</div>\n</Base>\n"
    out = format_epresso(src, expand=True)
    assert out == "<Base title={META['title']}>\n    <div class='a'>\n        <span>x</span>\n    </div>\n</Base>\n"
    # real lowercase void elements still never open a container
    assert format_epresso("<div class='a'>\n<img src='x.png'>\n<br>\n</div>\n", expand=True) == (
        "<div class='a'>\n    <img src='x.png'>\n    <br>\n</div>\n"
    )


def test_expand_keeps_prose_wrapping():
    """A prose element is re-emitted from source, not re-rendered: its internal
    line wrapping must survive (joining it gives 300-character lines)."""
    src = (
        '<div class="a">\n'
        "    <p>Some prose that the author\n"
        "       wrapped across lines.</p>\n"
        '    <span>{{ x }}</span>\n'
        "</div>\n"
    )
    out = format_epresso(src, expand=True)
    assert "Some prose that the author\n       wrapped across lines." in out
    assert "<span>\n        {{ x }}\n    </span>" in out

    nested = '<div class="o">\n<div class="m">\n<p>line one\n   line two</p>\n</div>\n</div>\n'
    out = format_epresso(nested, expand=True)
    # re-based, not flattened: the relative hanging indent is preserved
    assert "        <p>line one\n           line two</p>" in out


def test_expand_keeps_wrapped_tags_wrapped():
    """A long tag the author wrapped across lines keeps its wrapping."""
    src = (
        '<div class="a">\n'
        '<input type="checkbox" class="{{ BOX }}"\n'
        '       {% if props.name %}name="{{ props.name }}"{% endif %}\n'
        "       {% if props.checked %}checked{% endif %}>\n"
        "</div>\n"
    )
    out = format_epresso(src, expand=True)
    assert 'class="{{ BOX }}"\n           {% if props.name %}' in out
