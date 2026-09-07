"""Unit tests for the epresso document parser (front-matter + .ep blocks)."""

from epresso.document import parse_document, split_frontmatter, strip_frontmatter
from epresso.errors import ContentError


def test_markdown_frontmatter_decodes_without_timestamp_coercion():
    doc = parse_document("---\ntitle: Hi\ndate: 2026-01-01\n---\n\n# Body\n", "markdown")
    assert doc.kind == "markdown"
    assert doc.data == {"title": "Hi", "date": "2026-01-01"}
    assert doc.data["date"] == "2026-01-01"  # stays a string
    assert doc.body.strip() == "# Body"


def test_markdown_absent_frontmatter():
    doc = parse_document("# no front matter\n", "markdown")
    assert doc.data == {}
    assert doc.body == "# no front matter\n"


def test_empty_frontmatter_block():
    # `---\n---` — an empty block; the closing delimiter is at line start.
    doc = parse_document("---\n---\n<body>ok</body>\n", "markdown")
    assert doc.data == {}
    assert doc.body == "<body>ok</body>\n"


def test_frontmatter_value_with_inline_dashes_is_not_closed_mid_line():
    # A `---` inside a value must not close the block (only line-start --- does).
    doc = parse_document('---\ndescription: "a---b"\ntitle: T\n---\nbody\n', "markdown")
    assert doc.data == {"description": "a---b", "title": "T"}
    assert doc.body == "body\n"


def test_markdown_no_trailing_newline_after_closing():
    doc = parse_document("---\ntitle: T\n---", "markdown")
    assert doc.data == {"title": "T"}
    assert doc.body == ""


def test_markdown_invalid_yaml_raises_content_error():
    try:
        parse_document("---\n: :bad: yaml\n---\nbody\n", "markdown")
        raise AssertionError("expected ContentError")
    except ContentError:
        pass


def test_epresso_keeps_raw_frontmatter_and_extracts_blocks():
    raw = (
        "---\n"
        "from pydantic import BaseModel\n"
        "class Props(BaseModel):\n    title: str\n"
        "---\n"
        "<style scoped>.x{color:red}</style>\n"
        "<style is:global>.g{margin:0}</style>\n"
        "<script>window.x=1</script>\n"
        "<div>{{ props.title }}</div>\n"
    )
    doc = parse_document(raw, "ep")
    assert doc.kind == "ep"
    assert doc.data is None
    assert "class Props" in doc.frontmatter
    # style/script blocks are removed from the body
    assert "<style" not in doc.body
    assert "<script" not in doc.body
    assert doc.body.strip() == "<div>{{ props.title }}</div>"
    # scoped vs global classification
    assert ".x" in doc.scoped_css
    assert ".g" in doc.global_css
    assert ".x" not in doc.global_css
    assert "window.x" in doc.scripts


def test_epresso_inline_script_stays_in_body():
    # <script is:inline> is NOT extracted/bundled — it stays in the body so it
    # can run in the <head> before first paint (e.g. the theme pre-paint).
    raw = (
        "---\n---\n"
        "<script is:inline>var pre = 1;</script>\n"
        "<script>window.x = 1;</script>\n"
        "<div>hi</div>\n"
    )
    doc = parse_document(raw, "ep")
    assert "is:inline>var pre = 1;" in doc.body  # kept in the body
    assert "window.x" in doc.scripts  # non-inline extracted
    assert "var pre = 1" not in doc.scripts


def test_epresso_no_frontmatter():
    doc = parse_document("<div>hi</div>\n", "ep")
    assert doc.frontmatter == ""
    assert doc.body == "<div>hi</div>\n"


def test_strip_frontmatter_returns_body_only():
    assert strip_frontmatter("---\ntitle: T\n---\n# Body\n") == "# Body\n"
    assert strip_frontmatter("# no fm\n") == "# no fm\n"


def test_split_frontmatter_distinguishes_none_from_empty():
    assert split_frontmatter("body\n") == (None, "body\n")
    fm, body = split_frontmatter("---\n---\n<body></body>\n")
    assert fm == ""  # an empty block, not None
    assert body == "<body></body>\n"
