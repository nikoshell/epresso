"""Unit tests for the scoped-CSS transforms (epresso.scoped)."""

from epresso.scoped import inject_scope_attr, scope_css


def test_scope_css_scopes_each_selector():
    out = scope_css(".a { color: red } .b:hover { color: blue }", "abc")
    assert ".a[data-epresso-abc]" in out
    assert ".b[data-epresso-abc]:hover" in out  # attr before the pseudo


def test_scope_css_pseudo_before_attr_placement():
    out = scope_css(".a::before { content: '' }", "abc")
    assert ".a[data-epresso-abc]::before" in out


def test_scope_css_leaves_global_and_at_rules():
    css = "@media (min-width: 600px) { .x { color: red } } :global(.y) { color: blue }"
    out = scope_css(css, "abc")
    assert "@media" in out
    assert ".y[data-epresso-abc]" not in out  # :global(...) is an opt-out
    assert ".x[data-epresso-abc]" in out


def test_scope_css_ignores_bare_pseudo():
    out = scope_css(":hover { color: red }", "abc")
    assert ":hover" in out
    assert "[data-epresso-abc]" not in out


def test_inject_scope_attr_adds_to_element_open_tags():
    out = inject_scope_attr("<div class='x'><span>hi</span></div><img src='a'>", "abc")
    assert 'data-epresso-abc' in out
    # opening tags get the attr; closing tags do not
    assert "<div class='x' data-epresso-abc>" in out
    assert "</span>" in out


def test_inject_scope_attr_skips_style_script_doctype():
    html = "<!doctype html><style>.x{}</style><script>var a</script><p>hi</p>"
    out = inject_scope_attr(html, "abc")
    assert "<style>" in out
    assert "<script>" in out
    assert "<!doctype html>" in out
    assert "<p data-epresso-abc>" in out


def test_inject_scope_attr_skips_already_scoped_elements():
    # An element already carrying a scope (a child component's output) is left
    # untouched; only previously-unscoped elements get the new scope.
    html = "<div data-epresso-abc><span>hi</span></div>"
    out = inject_scope_attr(html, "xyz")
    div = __import__("re").search(r"<div[^>]*>", out).group(0)
    span = __import__("re").search(r"<span[^>]*>", out).group(0)
    assert "data-epresso-abc" in div and "data-epresso-xyz" not in div
    assert "data-epresso-xyz" in span


def test_scope_css_strips_global_pseudo():
    out = scope_css("article :global(h1){color:blue} :global(.y){margin:0}", "abc")
    assert "article[data-epresso-abc] h1" in out  # :global(h1) -> h1, article scoped
    assert ".y" in out and ".y[data-epresso-abc]" not in out  # :global(.y) -> .y, unscoped


def test_scope_css_leaves_keyframes_unscoped():
    out = scope_css("@keyframes fade{from{opacity:0} to{opacity:1}}", "abc")
    assert "from" in out and "to" in out
    assert "from[data-epresso-abc]" not in out  # keyframe selectors must not be scoped


def test_scope_css_recurses_into_media():
    out = scope_css("@media (min-width:600px){.x{color:green}}", "abc")
    assert ".x[data-epresso-abc]" in out  # rules inside @media are scoped


def test_scope_css_scopes_all_descendant_compounds():
    out = scope_css(".a .b:hover{color:red}", "abc")
    assert ".a[data-epresso-abc] .b[data-epresso-abc]:hover" in out  # both compounds scoped


def test_scope_css_where_strategy_is_zero_specificity():
    out = scope_css(".a{color:red}", "abc", strategy="where")
    assert ":where([data-epresso-abc])" in out
