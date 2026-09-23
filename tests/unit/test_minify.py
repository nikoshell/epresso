"""The safety guarantees `epresso.minify` relies on.

`minify_css` now runs over third-party output (postcss/UnoCSS), so what it keeps
matters as much as what it removes.
"""

from epresso.minify import minify_css, minify_html


def test_minify_css_keeps_license_banners():
    out = minify_css("/*! daisyUI 5 - MIT License */\n.a  {  color: red  }")
    assert out.startswith("/*! daisyUI 5 - MIT License */")
    assert ".a{color:red}" in out


def test_minify_css_drops_ordinary_comments():
    out = minify_css(".a { color: red } /* drop me */ .b { color: blue }")
    assert "drop me" not in out
    assert ".a{color:red}" in out


def test_minify_css_preserves_string_contents():
    out = minify_css('.a { content: "a  b"; font-family: "X  Y" }')
    assert '"a  b"' in out
    assert '"X  Y"' in out


def test_minify_css_preserves_calc_whitespace():
    out = minify_css(".a { width: calc(100% - 1rem) }")
    assert "calc(100% - 1rem)" in out


def test_minify_html_preserves_pre_and_script():
    html = "<div>  a  </div>\n<pre>  keep\n  this  </pre>\n<script>var a = 1;\n</script>"
    out = minify_html(html)
    assert "  keep\n  this  " in out
    assert "var a = 1;\n" in out


def test_minify_html_drops_comments():
    assert "secret" not in minify_html("<p>hi</p><!-- secret -->")


def test_minify_css_comment_with_a_quote_does_not_eat_later_rules():
    """A quote inside a comment once made the comment scan swallow real rules."""
    out = minify_css('/* it\'s a "note" */ .a { color: red } .b { color: blue }')
    assert ".a{color:red}" in out
    assert ".b{color:blue}" in out


def test_minify_css_keeps_a_comment_marker_inside_a_string():
    out = minify_css('.a { content: "/* not a comment */"; color: red } .b { color: blue }')
    assert '"/* not a comment */"' in out
    assert ".b{color:blue}" in out
