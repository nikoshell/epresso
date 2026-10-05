"""epresso_mkdocs: Material syntax renders with Material's markup (via `epresso docs`)."""

import re

from typer.testing import CliRunner

from epresso.cli import app

runner = CliRunner()

PAGE = """\
# Page

## Install { #setup .big }

!!! note "Heads up"
    Fence inside:

    ```py
    x = 1
    ```

    === "A"
        tab a

    === "B"
        tab b

???+ tip
    open details

Press ++ctrl+alt+del++, ==marked==, ^^ins^^, H~2~O, x^2^. The HTML spec.

*[HTML]: Hyper Text Markup Language

Term
:   Definition

- [x] done

Note[^1].

[^1]: a foot

--8<-- "snippets/part.md"

Lead paragraph {: .lead }
"""


def _build(tmp_path, monkeypatch, page=PAGE):
    (tmp_path / "docs").mkdir()
    (tmp_path / "snippets").mkdir()
    (tmp_path / "snippets" / "part.md").write_text("Snipped *text*.\n", encoding="utf-8")
    (tmp_path / "docs" / "index.md").write_text("# Home\n\nhi\n", encoding="utf-8")
    (tmp_path / "docs" / "page.md").write_text(page, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"
    result = runner.invoke(app, ["docs", ".", "--out", str(out)])
    return result, out


def test_material_syntax_renders(tmp_path, monkeypatch):
    result, out = _build(tmp_path, monkeypatch)
    assert result.exit_code == 0, result.output
    html = (out / "page" / "index.html").read_text(encoding="utf-8")
    body = re.sub(r" data-epresso-[0-9a-f]+", "", html[html.index('<article class="doc"') :])
    for needle in (
        'id="setup"', 'class="big"',
        '<div class="admonition note">', '<p class="admonition-title">Heads up</p>',
        'class="tabbed-set', '<label for="__tabbed_', '<details class="tip" open>', "<summary>Tip</summary>",
        '<kbd class="key-control">Ctrl</kbd>', "<mark>marked</mark>", "<ins>ins</ins>",
        "<sub>2</sub>", "<sup>2</sup>", '<abbr title="Hyper Text Markup Language">HTML</abbr>',
        "<dt>Term</dt>", "task-list-item-checkbox", 'class="footnote-ref"',
        "Snipped <em>text</em>.", '<p class="lead">',
    ):
        assert needle in body, needle
    assert "!!!" not in body and "--8&lt;--" not in body and "*[HTML]" not in body
    assert html.count('href="#setup"') >= 2  # heading anchor + ToC use the explicit id


def test_snippet_outside_project_is_an_error(tmp_path, monkeypatch):
    result, _ = _build(tmp_path, monkeypatch, page='# P\n\n--8<-- "../../etc/passwd"\n')
    assert result.exit_code != 0
    assert "outside the project" in result.output
