"""Tests for the components-over-Jinja composition enforcement (.ep authoring)."""

import pytest

from epresso.enforce import composition_violations, ensure_components
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
