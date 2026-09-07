"""Compression and <picture> tests."""

from epresso.minify import minify_html
from epresso.site import Site


# --- compression ------------------------------------------------------------
def test_minify_collapses_whitespace():
    out = minify_html("<!doctype html>\n<html>\n  <body>\n    <p>  hi  </p>\n  </body>\n</html>")
    assert "\n" not in out
    assert "hi" in out


def test_minify_preserves_prose_spaces():
    # a space between an inline tag and surrounding text is significant — never
    # strip it ("see <a>" / "</strong> bar" must not become "see<a>" / "bar")
    assert "see <a href=" in minify_html('see <a href="/x">link</a>')
    assert "</strong> bar" in minify_html("<p><strong>foo</strong> bar</p>")
    assert "</code> baz" in minify_html("<p>a</code> baz</p>")


def test_minify_preserves_pre_and_script():
    html = "<div>  a  </div><pre>\n  keep  me\n</pre><script>\nvar x = '  y  ';\n</script>"
    out = minify_html(html)
    assert "keep  me" in out  # preserved
    assert "var x" in out  # script preserved


def test_minify_css_preserves_descendant_combinator_before_pseudo():
    # a space before a pseudo-class (:hover, :not, ::before) is a descendant
    # combinator — minifying must NOT collapse it into a compound selector.
    from epresso.minify import minify_css

    assert ".prose :not(pre)>code" in minify_css(".prose :not(pre)>code { color: red }")
    assert ".a :hover" in minify_css(".a :hover { color: red }")


def test_compress_html_config(site):
    site.config.build.compress_html = True
    site.build()
    html = (site.config.dir_output() / "index.html").read_text()
    # home page minified: no newlines between tags
    assert "<!doctype html><html>" in html.replace(" ", "") or "\n" not in html.split("</title>")[1][:200]



# --- <picture> ---------------------------------------------------------------
def test_picture_renders_and_builds_webp_and_jpeg(tmp_path):
    from PIL import Image

    root = tmp_path
    (root / "assets" / "photos").mkdir(parents=True)
    im = Image.new("RGB", (1000, 500), (200, 30, 40))
    im.save(root / "assets" / "photos" / "hero.jpg", "JPEG")

    site = Site.load(root)
    html = site.images.picture("photos/hero.jpg", widths=[400, 800, 1000], alt="Hero")
    assert "<picture>" in html
    assert 'type="image/webp"' in html
    assert ".jpg " in html  # jpeg fallback srcset

    site.images.build(site.config.dir_output())
    out = site.config.dir_output()
    webp = [p for p in out.joinpath("images").rglob("*.webp")]
    jpg = [p for p in out.joinpath("images").rglob("*.jpg")]
    assert len(webp) == 3 and len(jpg) == 3
