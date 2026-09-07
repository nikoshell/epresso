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
