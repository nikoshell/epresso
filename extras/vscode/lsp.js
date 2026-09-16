"use strict";

// Minimal, dependency-free LSP client for the `epresso lsp` server.
//
// Only the subset the extension needs: `initialize`, full-document sync
// (`didOpen`/`didChange`/`didClose`) and `textDocument/publishDiagnostics`.
// Kept separate from extension.js (and free of any `vscode` import) so it can be
// exercised with plain Node against the real server.

const { spawn } = require("child_process");

const HEADER_SEPARATOR = "\r\n\r\n";

class EpressoLspClient {
  /**
   * @param {{command?: string, args?: string[], cwd?: string, rootUri?: string|null,
   *          onDiagnostics: (uri: string, diagnostics: any[]) => void,
   *          onError: (error: Error) => void}} options
   */
  constructor(options) {
    this.command = options.command || "epresso";
    this.args = options.args || ["lsp"];
    this.cwd = options.cwd;
    this.rootUri = options.rootUri || null;
    this.onDiagnostics = options.onDiagnostics;
    this.onError = options.onError || (() => {});

    this.child = null;
    this.buffer = Buffer.alloc(0);
    this.nextId = 1;
    this.pending = new Map();
    this.open = new Map();
    this.queue = [];
    this.initialized = false;
    this.failed = false;
    this.disposed = false;
  }

  start() {
    this.child = spawn(this.command, this.args, { cwd: this.cwd });
    this.child.on("error", (err) => this._fail(err));
    this.child.on("exit", (code) => {
      if (!this.disposed) {
        this._fail(new Error(`epresso lsp exited (code ${code})`));
      }
    });
    this.child.stdout.on("data", (chunk) => this._onData(chunk));
    this.child.stderr.on("data", () => {});

    this._request("initialize", {
      processId: process.pid,
      rootUri: this.rootUri,
      capabilities: { textDocument: { synchronize: {} } },
    })
      .then(() => {
        this.initialized = true;
        this._send({ jsonrpc: "2.0", method: "initialized", params: {} });
        for (const message of this.queue) {
          this._send(message);
        }
        this.queue = [];
      })
      .catch((err) => this._fail(err));
    return this;
  }

  openDocument(uri, text) {
    this.open.set(uri, text);
    this._notify("textDocument/didOpen", {
      textDocument: { uri, languageId: "epresso", version: 1, text },
    });
  }

  changeDocument(uri, text) {
    if (!this.open.has(uri)) {
      return this.openDocument(uri, text);
    }
    this.open.set(uri, text);
    this._notify("textDocument/didChange", {
      textDocument: { uri, version: 2 },
      contentChanges: [{ text }],
    });
  }

  closeDocument(uri) {
    this.open.delete(uri);
    this._notify("textDocument/didClose", { textDocument: { uri } });
  }

  dispose() {
    this.disposed = true;
    if (this.child && this.child.exitCode === null) {
      try {
        this._request("shutdown", {}).finally(() => {
          this._notify("exit", {});
          if (this.child) {
            this.child.kill();
          }
        });
      } catch {
        this.child.kill();
      }
    }
  }

  // -- internals ------------------------------------------------------------

  _send(message) {
    if (!this.child || !this.child.stdin.writable) {
      return;
    }
    const body = Buffer.from(JSON.stringify(message), "utf8");
    this.child.stdin.write(`Content-Length: ${body.length}${HEADER_SEPARATOR}`);
    this.child.stdin.write(body);
  }

  _notify(method, params) {
    const message = { jsonrpc: "2.0", method, params };
    // LSP forbids notifications before the initialize response; queue them.
    if (!this.initialized) {
      this.queue.push(message);
      return;
    }
    this._send(message);
  }

  _request(method, params) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this._send({ jsonrpc: "2.0", id, method, params });
    });
  }

  _onData(chunk) {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    for (;;) {
      const separator = this.buffer.indexOf(HEADER_SEPARATOR);
      if (separator < 0) {
        return;
      }
      const header = this.buffer.slice(0, separator).toString("ascii");
      const match = /Content-Length:\s*(\d+)/i.exec(header);
      const start = separator + HEADER_SEPARATOR.length;
      if (!match) {
        this.buffer = this.buffer.slice(start);
        continue;
      }
      const length = parseInt(match[1], 10);
      if (this.buffer.length < start + length) {
        return;
      }
      const body = this.buffer.slice(start, start + length).toString("utf8");
      this.buffer = this.buffer.slice(start + length);
      let message;
      try {
        message = JSON.parse(body);
      } catch {
        continue; // ignore a malformed frame rather than killing the session
      }
      this._handle(message);
    }
  }

  _handle(message) {
    if (message.id !== undefined && this.pending.has(message.id)) {
      const pending = this.pending.get(message.id);
      this.pending.delete(message.id);
      if (message.error) {
        pending.reject(new Error(message.error.message || "lsp error"));
      } else {
        pending.resolve(message.result);
      }
      return;
    }
    if (message.method === "textDocument/publishDiagnostics") {
      this.onDiagnostics(message.params.uri, message.params.diagnostics || []);
    }
  }

  _fail(error) {
    if (this.failed) {
      return;
    }
    this.failed = true;
    this.onError(error);
  }
}

module.exports = { EpressoLspClient };
