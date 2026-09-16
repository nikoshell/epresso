"""Tests for the components-over-Jinja composition enforcement (.ep authoring)."""

import pytest

from epresso.document import SidecarBlocks, parse_document
from epresso.enforce import (
    composition_violations,
    ensure_components,
    ensure_ep_structure,
    sidecar_violations,
    structure_violations,
)
from epresso.errors import TemplateError


def test_allows_component_syntax_and_control_flow():
    body = """<Base title="X">
{% if repo %}<a href="{{ repo }}">{% endif %}
{% for h in props.headings %}<p>{{ h }}</p>{% endfor %}
{# a comment {% include %} is ignored #}
<!-- {% extends %} commented out -->
<slot/>
</Base>
"""
    assert composition_violations(body) == []


@pytest.mark.parametrize(
    "directive",
    ["extends", "block", "include", "component", "macro", "import", "from", "call"],
)
def test_flags_forbidden_directive(directive):
    body = "{% " + directive + " 'x' %}"
    (found,) = composition_violations(body)
    assert found[0] == directive


def test_reports_line_number():
    body = "line one\n{% block content %}hi{% endblock %}\n"
    violations = composition_violations(body)
    assert ("block", 2) in violations


def test_ensure_components_raises_with_path_and_fix():
    with pytest.raises(TemplateError) as exc:
        ensure_components("{% include 'nav' %}", label="pages/index.ep")
    msg = str(exc.value)
    assert "pages/index.ep" in msg
    assert "include" in msg
    assert "<Component/" in msg  # remediation hint present


def test_ensure_components_passes_clean_body():
    ensure_components("<Header />{{ title }}\n", label="pages/index.ep")  # no raise


# ── .ep file shape: one root per branch ──────────────────────────────────


@pytest.mark.parametrize(
    "body",
    [
        "<div>x</div>",
        "<img src='x.png'>",
        "<Base><slot/></Base>",
        "<slot/>",
        "{{ content }}",
        "hello",
        "<Fragment><div>a</div><aside>b</aside></Fragment>",
        "<><div>a</div><aside>b</aside></>",
        "<></>",
        "{% if x %}<a>y</a>{% else %}<></>{% endif %}",
        "{% if x %}<a>y</a>{% endif %}",  # implicit empty branch renders nothing
        "{% if x %}<a>y</a>{% elif z %}<b>y</b>{% endif %}",
        "{% for h in hs %}<li>{{ h }}</li>{% endfor %}",
        "{% for h in hs %}{% if h %}<li>x</li>{% endif %}{% endfor %}",
        "<div>{% if x %}a{% endif %}</div>",  # control flow inside a root
    ],
)
def test_structure_accepts(body):
    assert structure_violations(body) == []


@pytest.mark.parametrize(
    "body",
    [
        "<div>a</div><aside>b</aside>",
        "{{ a }}<div>b</div>",
        "Hello <div>x</div>",
    ],
)
def test_structure_flags_two_roots(body):
    (line, msg), = structure_violations(body)
    assert line == 1
    assert "2 roots in the same branch" in msg
    assert "<Fragment>" in msg


@pytest.mark.parametrize(
    "body",
    [
        "{% if x %}{% else %}<a>y</a>{% endif %}",  # explicit empty if branch
        "{% if x %}<a>y</a>{% else %}{% endif %}",  # explicit empty else branch
    ],
)
def test_structure_flags_empty_branch(body):
    (_line, msg), = structure_violations(body)
    assert "renders no root" in msg


def test_structure_reports_the_second_root_line():
    (line, _msg), = structure_violations("<p>a</p>\n<p>b</p>\n")
    assert line == 2


def test_sidecar_violations_cap_per_kind():
    assert sidecar_violations(SidecarBlocks((5,), (7,), (9,))) == []
    assert sidecar_violations(SidecarBlocks((5, 9), (), ())) == [
        (9, "2 scoped <style> blocks — merge them into one")
    ]
    assert sidecar_violations(SidecarBlocks((), (), (3, 4))) == [
        (4, "2 <script> blocks — merge them into one")
    ]
    assert sidecar_violations(SidecarBlocks((), (2, 5), ())) == [
        (5, "2 <style is:global> blocks — merge them into one")
    ]


def test_ensure_ep_structure_raises_with_path_line_and_fix():
    doc = parse_document("---\n---\n<div>a</div><aside>b</aside>\n", "ep")
    with pytest.raises(TemplateError) as exc:
        ensure_ep_structure(doc, label="components/Side.ep")
    msg = str(exc.value)
    assert "components/Side.ep" in msg
    assert "line 3" in msg
    assert "<Fragment>" in msg  # remediation hint


def test_ensure_ep_structure_reports_every_problem():
    src = (
        "---\n---\n"
        "<style>.a{}</style>\n"
        "<style>.b{}</style>\n"
        "<div>x</div><p>y</p>\n"
    )
    doc = parse_document(src, "ep")
    with pytest.raises(TemplateError) as exc:
        ensure_ep_structure(doc, label="components/Two.ep")
    msg = str(exc.value)
    assert "2 problem(s)" in msg
    assert "scoped <style> blocks" in msg
    assert "roots in the same branch" in msg
    assert "one scoped <style>" in msg  # sidecar fix hint


def test_ensure_ep_structure_passes_single_root():
    doc = parse_document("---\n---\n<div>x</div>\n", "ep")
    ensure_ep_structure(doc, label="components/One.ep")  # no raise
