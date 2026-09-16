"""End-to-end test for ``epresso lsp``: a real subprocess speaking framed JSON-RPC."""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading

from epresso.lsp import read_message, write_message


class _Reader:
    """Read framed messages off a pipe in a thread so the test can time out."""

    def __init__(self, stream) -> None:  # noqa: ANN001
        self.messages: queue.Queue = queue.Queue()
        self._stop = False
        threading.Thread(target=self._run, args=(stream,), daemon=True).start()

    def _run(self, stream) -> None:  # noqa: ANN001
        while not self._stop:
            try:
                message = read_message(stream)
            except Exception:  # noqa: BLE001
                break
            if message is None:
                break
            self.messages.put(message)

    def get(self, timeout: float = 10.0) -> dict:
        return self.messages.get(timeout=timeout)

    def stop(self) -> None:
        self._stop = True


def _spawn() -> subprocess.Popen:
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    return subprocess.Popen(
        [sys.executable, "-m", "epresso", "lsp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )


def test_lsp_server_over_stdio():
    proc = _spawn()
    reader = _Reader(proc.stdout)
    try:
        write_message(proc.stdin, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        init = reader.get()
        assert init["id"] == 1
        assert init["result"]["capabilities"]["documentFormattingProvider"] is True

        write_message(proc.stdin, {"jsonrpc": "2.0", "method": "initialized", "params": {}})

        write_message(
            proc.stdin,
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": "file:///t.ep",
                        "languageId": "epresso",
                        "version": 1,
                        "text": "---\n---\n<div>a</div><aside>b</aside>\n",
                    }
                },
            },
        )
        note = reader.get()
        assert note["method"] == "textDocument/publishDiagnostics"
        assert [d["code"] for d in note["params"]["diagnostics"]] == ["file-shape"]

        # A full-sync edit clears the diagnostics and gives the formatter new text.
        src = "<style>.a{color:red}</style>\n<div>x</div>\n"
        write_message(
            proc.stdin,
            {
                "jsonrpc": "2.0",
                "method": "textDocument/didChange",
                "params": {
                    "textDocument": {"uri": "file:///t.ep", "version": 2},
                    "contentChanges": [{"text": src}],
                },
            },
        )
        assert reader.get()["params"]["diagnostics"] == []

        write_message(
            proc.stdin,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "textDocument/formatting",
                "params": {"textDocument": {"uri": "file:///t.ep"}, "options": {}},
            },
        )
        response = reader.get()
        assert response["id"] == 2
        (edit,) = response["result"]
        assert edit["newText"].startswith("<div>x</div>")

        write_message(proc.stdin, {"jsonrpc": "2.0", "id": 3, "method": "shutdown", "params": {}})
        assert reader.get()["id"] == 3
        write_message(proc.stdin, {"jsonrpc": "2.0", "method": "exit", "params": {}})
        assert proc.wait(timeout=10) == 0
    finally:
        reader.stop()
        if proc.poll() is None:
            proc.kill()
