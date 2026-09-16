"""Tests for the .ep Language Server (`epresso lsp`)."""

from __future__ import annotations

from epresso.fmt import format_text
from epresso.lsp import Server, compute_diagnostics, formatting_edits


def _codes(diags: list[dict]) -> list[str]:
    return [d["code"] for d in diags]


def test_clean_component_has_no_diagnostics():
    src = (
        "---\n"
        "from pydantic import BaseModel\n"
        "class Props(BaseModel):\n"
        "    title: str = ''\n"
        "---\n"
        "<Base title={props.title}><h1>{{ props.title }}</h1></Base>\n"
    )
    assert compute_diagnostics(src) == []


def test_forbidden_directive_is_reported_at_file_line():
    src = "---\n---\n<p>ok</p>\n{% include 'nav' %}\n"
    (diag,) = compute_diagnostics(src)
    assert diag["code"] == "composition"
    assert diag["range"]["start"]["line"] == 3  # frontmatter occupies 2 lines
    assert "include" in diag["message"]
    assert diag["severity"] == 1
    assert diag["source"] == "epresso"


def test_two_roots_is_reported_as_file_shape():
    src = "---\n---\n<div>a</div><aside>b</aside>\n"
    (diag,) = compute_diagnostics(src)
    assert diag["code"] == "file-shape"
    assert diag["range"]["start"]["line"] == 2
    assert "2 roots" in diag["message"]


def test_sidecar_cap_is_reported():
    src = "---\n---\n<div>x</div>\n<style>.a{color:red}</style>\n<style>.b{color:blue}</style>\n"
    (diag,) = compute_diagnostics(src)
    assert diag["code"] == "sidecar"
    assert "2 scoped <style>" in diag["message"]
    assert diag["range"]["start"]["line"] == 4


def test_frontmatter_syntax_error_is_reported():
    src = "---\ndef broken(:\n---\n<p>x</p>\n"
    diags = compute_diagnostics(src)
    assert "syntax" in _codes(diags)
    assert any("syntax error" in d["message"] for d in diags)


def test_endpoint_body_is_not_shape_checked():
    src = "---\ndef get():\n    return 'text/html', '<p>x</p><p>y</p>'\n---\n<div>a</div><aside>b</aside>\n"
    assert compute_diagnostics(src) == []


def test_diagnostics_never_point_past_the_file():
    src = "---\n---\n"
    for diag in compute_diagnostics(src):
        assert 0 <= diag["range"]["start"]["line"] < max(1, len(src.splitlines()))


def test_formatting_edits_replace_the_document():
    src = "<style>.a{color:red}</style>\n<div>x</div>\n"
    (edit,) = formatting_edits(src)
    assert edit["newText"] == format_text(src)
    assert edit["range"]["start"] == {"line": 0, "character": 0}
    assert edit["range"]["end"]["line"] == src.count("\n")


def test_formatting_edits_empty_when_already_canonical():
    assert formatting_edits(format_text("<style>.a{color:red}</style>\n<div>x</div>\n")) == []


def test_server_initialize_advertises_capabilities():
    response, notifications = Server().handle(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    assert notifications == []
    capabilities = response["result"]["capabilities"]
    assert capabilities["textDocumentSync"] == 1
    assert capabilities["documentFormattingProvider"] is True
    assert response["result"]["serverInfo"]["name"] == "epresso"


def test_server_did_open_publishes_diagnostics():
    server = Server()
    server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    _, notes = server.handle(
        {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {"textDocument": {"uri": "file:///a.ep", "text": "---\n---\n<div>a</div><aside>b</aside>\n"}},
        }
    )
    (note,) = notes
    assert note["method"] == "textDocument/publishDiagnostics"
    assert note["params"]["uri"] == "file:///a.ep"
    assert _codes(note["params"]["diagnostics"]) == ["file-shape"]


def test_server_formatting_returns_whole_document_edit():
    server = Server()
    src = "<style>.a{color:red}</style>\n<div>x</div>\n"
    server.handle(
        {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {"textDocument": {"uri": "file:///a.ep", "text": src}},
        }
    )
    response, _ = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "textDocument/formatting",
            "params": {"textDocument": {"uri": "file:///a.ep"}, "options": {}},
        }
    )
    (edit,) = response["result"]
    assert edit["newText"] == format_text(src)


def test_server_unknown_method_is_an_error():
    response, _ = Server().handle({"jsonrpc": "2.0", "id": 9, "method": "textDocument/hover", "params": {}})
    assert response["error"]["code"] == -32601


def test_server_shutdown_and_exit():
    server = Server()
    server.handle({"jsonrpc": "2.0", "id": 1, "method": "shutdown", "params": {}})
    assert server.shutdown is True
    server.handle({"jsonrpc": "2.0", "method": "exit", "params": {}})
    assert server.exit is True
