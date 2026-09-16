"""``epresso lsp`` — a dependency-free Language Server for ``.ep`` files.

JSON-RPC 2.0 over stdio (``Content-Length`` framed), implemented with the
standard library only, so ``epresso`` carries no LSP dependency. It reuses the
same rules the build enforces, which means the editor and the build agree:

* **diagnostics** — forbidden Jinja composition directives, the
  one-root-per-branch file shape, per-kind sidecar caps, and Python syntax
  errors in the frontmatter;
* **formatting** — the canonical ``epresso fmt`` output for the whole document.

Any LSP-capable editor can use it (Neovim's built-in client, VS Code via the
bundled extension, Emacs, …)::

    epresso lsp        # speaks LSP on stdin/stdout
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, BinaryIO
from urllib.request import url2pathname

from . import __version__
from .document import parse_document
from .enforce import composition_violations, sidecar_violations, structure_violations
from .fmt import format_full, format_text
from .logger import get_logger

__all__ = ["Server", "compute_diagnostics", "formatting_edits", "read_message", "serve", "write_message"]

log = get_logger("lsp")

# An ``.ep`` endpoint exports ``get()`` — its body is generated, never rendered,
# so the file-shape/composition rules do not apply to it (mirrors the build).
_ENDPOINT = re.compile(r"^\s*def\s+get\s*\(", re.M)

_ERROR = 1  # LSP DiagnosticSeverity.Error


# -- JSON-RPC framing -------------------------------------------------------


def read_message(stream: BinaryIO) -> dict[str, Any] | None:
    """Read one ``Content-Length`` framed JSON-RPC message, or None at EOF."""
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        name, _, value = line.decode("ascii", "replace").partition(":")
        if name:
            headers[name.strip().lower()] = value.strip()
    try:
        length = int(headers.get("content-length", "0"))
    except ValueError:
        return None
    if length <= 0:
        return None
    body = stream.read(length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def write_message(stream: BinaryIO, payload: dict[str, Any]) -> None:
    """Write one ``Content-Length`` framed JSON-RPC message."""
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    stream.write(b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n" + body)
    stream.flush()


# -- diagnostics ------------------------------------------------------------


def _range(line: int, start: int, end: int) -> dict[str, Any]:
    return {"start": {"line": line, "character": start}, "end": {"line": line, "character": end}}


def compute_diagnostics(text: str) -> list[dict[str, Any]]:
    """LSP diagnostics for one ``.ep`` source (0-based lines).

    Lines mirror the build's own error reporting: structural lines come from the
    extracted body, sidecar lines from the original body, both shifted by the
    frontmatter offset — and clamped to the file so a diagnostic can never point
    past the end while the user is typing.
    """
    diags: list[dict[str, Any]] = []
    try:
        doc = parse_document(text, "ep")
    except Exception as e:  # noqa: BLE001 — a broken document must not kill the server
        return [
            {
                "range": _range(0, 0, 0),
                "severity": _ERROR,
                "source": "epresso",
                "code": "parse",
                "message": f"could not parse .ep source: {e}",
            }
        ]

    file_lines = text.splitlines()

    def diag(file_line_1based: int, message: str, code: str) -> dict[str, Any]:
        line = min(max(0, file_line_1based - 1), max(0, len(file_lines) - 1))
        width = len(file_lines[line]) if file_lines else 0
        return {
            "range": _range(line, 0, width),
            "severity": _ERROR,
            "source": "epresso",
            "code": code,
            "message": message,
        }

    frontmatter = doc.frontmatter or ""
    if frontmatter.strip():
        # compile() only — never exec() a user file on every keystroke.
        try:
            compile(frontmatter, "<frontmatter>", "exec", dont_inherit=True)
        except SyntaxError as e:
            line = max(0, (e.lineno or 1) - 1)
            width = len(file_lines[line]) if line < len(file_lines) else 0
            diags.append(
                {
                    "range": _range(line, 0, width),
                    "severity": _ERROR,
                    "source": "epresso",
                    "code": "syntax",
                    "message": f"Python syntax error in frontmatter: {e.msg}",
                }
            )

    if _ENDPOINT.search(frontmatter):
        return diags  # endpoint body is generated content, not a rendered template

    offset = doc.line_offset
    for directive, body_line in composition_violations(doc.body):
        diags.append(
            diag(
                body_line + offset,
                f"`{{% {directive} %}}` is not allowed in a .ep file — compose with components and <slot/> instead",
                "composition",
            )
        )
    for body_line, message in structure_violations(doc.body):
        diags.append(diag(body_line + offset, message, "file-shape"))
    for body_line, message in sidecar_violations(doc.sidecars):
        diags.append(diag(body_line + offset, message, "sidecar"))

    diags.sort(key=lambda d: (d["range"]["start"]["line"], d["range"]["start"]["character"]))
    return diags


# -- formatting -------------------------------------------------------------


def _end_position(text: str) -> dict[str, int]:
    line = text.count("\n")
    return {"line": line, "character": len(text) - (text.rfind("\n") + 1)}


def formatting_edits(text: str, *, expand: bool = False, full: bool = False) -> list[dict[str, Any]]:
    """A single whole-document TextEdit in the canonical ``epresso fmt`` form."""
    formatted = format_full(text, expand=expand or full) if full else format_text(text, expand=expand)
    if formatted == text:
        return []
    return [{"range": {"start": {"line": 0, "character": 0}, "end": _end_position(text)}, "newText": formatted}]


def _file_uri_to_path(uri: str) -> Path | None:
    if not uri.startswith("file://"):
        return None
    tail = uri[len("file://") :]
    if tail.startswith("/") and len(tail) > 2 and tail[2] == ":":  # file:///C:/x
        tail = tail[1:]
    return Path(url2pathname(tail))


# -- server -----------------------------------------------------------------


class _RpcError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


class Server:
    """Stateful LSP server: full-sync documents + diagnostics + formatting."""

    def __init__(self) -> None:
        self.documents: dict[str, str] = {}
        self.expand = False
        self.full = False
        self.shutdown = False
        self.exit = False

    # -- dispatch -----------------------------------------------------------
    def handle(self, message: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Return ``(response_or_None, notifications)`` for one message."""
        method = message.get("method")
        params = message.get("params") or {}
        msg_id = message.get("id")
        try:
            result, notifications = self._dispatch(method, params)
        except _RpcError as e:
            if msg_id is None:
                return None, []
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": e.code, "message": str(e)}}, []
        except Exception as e:  # noqa: BLE001 — never take the server down
            log.debug(f"internal error handling {method}: {e}")
            if msg_id is None:
                return None, []
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": str(e)}}, []
        if msg_id is None:
            return None, notifications
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}, notifications

    def _dispatch(self, method: Any, params: dict[str, Any]) -> tuple[Any, list[dict[str, Any]]]:
        if method == "initialize":
            options = params.get("initializationOptions") or {}
            fmt = options.get("format") or {}
            self.expand = bool(fmt.get("expand"))
            self.full = bool(fmt.get("full"))
            return (
                {
                    "capabilities": {"textDocumentSync": 1, "documentFormattingProvider": True},
                    "serverInfo": {"name": "epresso", "version": __version__},
                },
                [],
            )
        if method == "initialized":
            return None, []
        if method == "shutdown":
            self.shutdown = True
            return None, []
        if method == "exit":
            self.exit = True
            return None, []
        if method == "textDocument/didOpen":
            document = params["textDocument"]
            uri = document["uri"]
            self.documents[uri] = document.get("text", "")
            return None, [self._publish(uri)]
        if method == "textDocument/didChange":
            uri = params["textDocument"]["uri"]
            changes = params.get("contentChanges") or []
            if changes:
                self.documents[uri] = changes[-1]["text"]  # full sync
            return None, [self._publish(uri)]
        if method == "textDocument/didClose":
            uri = params["textDocument"]["uri"]
            self.documents.pop(uri, None)
            cleared = {"uri": uri, "diagnostics": []}
            return None, [{"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics", "params": cleared}]
        if method == "textDocument/formatting":
            uri = params["textDocument"]["uri"]
            text = self.documents.get(uri)
            if text is None:
                path = _file_uri_to_path(uri)
                text = path.read_text(encoding="utf-8") if path and path.is_file() else ""
            return formatting_edits(text, expand=self.expand, full=self.full), []
        if method in ("$/cancelRequest", "workspace/didChangeConfiguration"):
            return None, []
        raise _RpcError(-32601, f"method not found: {method}")

    def _publish(self, uri: str) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": uri, "diagnostics": compute_diagnostics(self.documents[uri])},
        }


def serve(stdin: BinaryIO | None = None, stdout: BinaryIO | None = None) -> int:
    """Run the server over stdio until EOF / ``exit``. Returns an exit code."""
    inp = stdin if stdin is not None else sys.stdin.buffer
    out = stdout if stdout is not None else sys.stdout.buffer
    server = Server()
    while True:
        try:
            message = read_message(inp)
        except Exception as e:  # noqa: BLE001 — malformed frame ends the session
            log.debug(f"closing on malformed message: {e}")
            return 1
        if message is None:
            return 0
        response, notifications = server.handle(message)
        for notification in notifications:
            write_message(out, notification)
        if response is not None:
            write_message(out, response)
        if server.exit:
            return 0
