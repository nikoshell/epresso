"""Unit tests for the shared JSX-style attribute parser."""

from epresso.jsxattrs import Expr, parse_jsx_attrs


def test_quoted_strings():
    assert parse_jsx_attrs('title="Hi"') == [("title", "Hi")]
    assert parse_jsx_attrs("title='Hi'") == [("title", "Hi")]


def test_braced_expression_is_an_expr():
    (key, value), = parse_jsx_attrs("count={items|length}")
    assert key == "count"
    assert isinstance(value, Expr)
    assert value == "items|length"


def test_bare_boolean():
    assert parse_jsx_attrs("disabled") == [("disabled", True)]


def test_mixed_run():
    attrs = parse_jsx_attrs('title="Hi" count={n} disabled layout="three"')
    assert attrs == [
        ("title", "Hi"),
        ("count", Expr("n")),
        ("disabled", True),
        ("layout", "three"),
    ]


def test_dashed_and_underscore_keys():
    attrs = parse_jsx_attrs('data-foo="1" data_bar="2"')
    assert attrs == [("data-foo", "1"), ("data_bar", "2")]


def test_expr_keeps_inner_text_verbatim():
    (_, value), = parse_jsx_attrs("x={ a + b }")
    assert value == " a + b "  # callers choose whether to strip
