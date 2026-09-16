"use strict";

// Epresso VS Code extension.
//
// Two independent features:
//
//   1. Formatting — "Format Document" pipes the buffer to `epresso fmt --stdin`
//      (no temp files) and replaces the document with the canonical output.
//   2. Diagnostics — a small LSP client (`./lsp.js`) runs `epresso lsp` and
//      shows the same rules the build enforces (forbidden Jinja composition,
//      the one-root-per-branch file shape, sidecar caps, frontmatter syntax).
//
// Both shell out to the `epresso` CLI, so a missing binary degrades to a clear
// message and leaves the buffer untouched.

const vscode = require("vscode");
const { spawn } = require("child_process");
const { EpressoLspClient } = require("./lsp");

/**
 * Run a command, write `input` to its stdin, and resolve with stdout.
 * Rejects on a non-zero exit or a spawn error (e.g. ENOENT).
 *
 * @param {string} command
 * @param {string[]} args
 * @param {string} input
 * @param {string|undefined} cwd
 * @returns {Promise<string>}
 */
function run(command, args, input, cwd) {
  return new Promise((resolve, reject) => {
    let child;
    try {
      child = spawn(command, args, { cwd });
    } catch (err) {
      reject(err);
      return;
    }

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => (stdout += chunk));
    child.stderr.on("data", (chunk) => (stderr += chunk));
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(stderr.trim() || `${command} exited with code ${code}`));
      }
    });

    // Ignore EPIPE if the child exits before we finish writing.
    child.stdin.on("error", () => {});
    child.stdin.end(input);
  });
}

/** @param {vscode.ExtensionContext} context */
function activate(context) {
  registerFormatter(context);
  registerDiagnostics(context);
}

/** @param {vscode.ExtensionContext} context */
function registerFormatter(context) {
  context.subscriptions.push(
    vscode.languages.registerDocumentFormattingEditProvider(
      { language: "epresso" },
      {
        /**
         * @param {vscode.TextDocument} document
         * @returns {Promise<vscode.TextEdit[]>}
         */
        async provideDocumentFormattingEdits(document) {
          const config = vscode.workspace.getConfiguration("epresso", document.uri);
          const executablePath = config.get("format.executablePath", "epresso");
          const args = ["fmt", "--stdin"];
          if (config.get("format.expand", false)) {
            args.push("--expand");
          }
          if (config.get("format.full", false)) {
            args.push("--full");
          }

          const input = document.getText();
          const folder = vscode.workspace.getWorkspaceFolder(document.uri);
          let output;
          try {
            output = await run(executablePath, args, input, folder && folder.uri.fsPath);
          } catch (err) {
            const missing = err && (err.code === "ENOENT" || /ENOENT/.test(String(err.message)));
            const message = missing
              ? `Epresso formatter not found: '${executablePath}'. Set "epresso.format.executablePath" or install the epresso CLI.`
              : `epresso fmt failed: ${err.message}`;
            vscode.window.showErrorMessage(message);
            return [];
          }

          if (output === input) {
            return [];
          }
          const fullRange = new vscode.Range(document.positionAt(0), document.positionAt(input.length));
          return [vscode.TextEdit.replace(fullRange, output)];
        },
      }
    )
  );
}

/** @param {vscode.ExtensionContext} context */
function registerDiagnostics(context) {
  const collection = vscode.languages.createDiagnosticCollection("epresso");
  context.subscriptions.push(collection);

  const config = () => vscode.workspace.getConfiguration("epresso");
  if (!config().get("lsp.enable", true)) {
    return;
  }

  const folder = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0];
  let errorShown = false;
  const client = new EpressoLspClient({
    command: config().get("lsp.executablePath", "epresso"),
    args: ["lsp"],
    cwd: folder && folder.uri.fsPath,
    rootUri: folder ? folder.uri.toString() : null,
    onDiagnostics: (uri, diagnostics) => {
      collection.set(vscode.Uri.parse(uri), diagnostics.map(toVscodeDiagnostic));
    },
    onError: (err) => {
      if (!errorShown) {
        errorShown = true;
        vscode.window.showWarningMessage(`Epresso language server unavailable: ${err.message}`);
      }
    },
  });
  context.subscriptions.push({ dispose: () => client.dispose() });

  const isEpresso = (document) => document.languageId === "epresso";
  const timers = new Map();

  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument((document) => {
      if (isEpresso(document)) {
        client.openDocument(document.uri.toString(), document.getText());
      }
    }),
    vscode.workspace.onDidChangeTextDocument((event) => {
      const document = event.document;
      if (!isEpresso(document)) {
        return;
      }
      const key = document.uri.toString();
      if (timers.has(key)) {
        clearTimeout(timers.get(key));
      }
      timers.set(
        key,
        setTimeout(() => {
          timers.delete(key);
          client.changeDocument(key, document.getText());
        }, 150)
      );
    }),
    vscode.workspace.onDidCloseTextDocument((document) => {
      if (isEpresso(document)) {
        const key = document.uri.toString();
        client.closeDocument(key);
        collection.delete(document.uri);
      }
    })
  );

  for (const document of vscode.workspace.textDocuments) {
    if (isEpresso(document)) {
      client.openDocument(document.uri.toString(), document.getText());
    }
  }
  client.start();
}

/**
 * @param {any} diagnostic an LSP Diagnostic
 * @returns {vscode.Diagnostic}
 */
function toVscodeDiagnostic(diagnostic) {
  const { start, end } = diagnostic.range;
  const range = new vscode.Range(start.line, start.character, end.line, end.character);
  const severity =
    diagnostic.severity === 1 ? vscode.DiagnosticSeverity.Error : vscode.DiagnosticSeverity.Warning;
  const result = new vscode.Diagnostic(range, diagnostic.message, severity);
  result.source = diagnostic.source || "epresso";
  if (diagnostic.code !== undefined) {
    result.code = diagnostic.code;
  }
  return result;
}

function deactivate() {}

module.exports = { activate, deactivate };
