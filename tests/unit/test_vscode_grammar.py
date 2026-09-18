"""Structural checks for the bundled VS Code extension (`extras/vscode`).

There is no Node toolchain in CI, so this validates the extension's JSON rather
than running it: the manifest points at real files, the grammars parse, and every
``include`` resolves to a repository rule in the same grammar or a known built-in
scope. That catches the common "renamed a rule, broke the grammar" mistake.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

VSCODE = Path(__file__).resolve().parents[2] / "extras" / "vscode"
GRAMMARS = [
    VSCODE / "syntaxes" / "epresso.tmLanguage.json",
    VSCODE / "syntaxes" / "epresso-injection.tmLanguage.json",
]

# Scopes VS Code ships (the extension embeds these).
EXTERNAL = {"text.html.basic", "source.python", "source.css", "source.js"}


def _includes(node: Any) -> list[str]:
    """Every ``include`` string anywhere in a grammar tree."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "include" and isinstance(value, str):
                found.append(value)
            else:
                found.extend(_includes(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_includes(item))
    return found


def test_manifest_points_at_real_files():
    pkg = json.loads((VSCODE / "package.json").read_text(encoding="utf-8"))
    grammars = pkg["contributes"]["grammars"]

    languages = {lang["id"]: lang for lang in pkg["contributes"]["languages"]}
    assert "epresso" in languages
    assert ".ep" in languages["epresso"]["extensions"]
    assert (VSCODE / "extension.js").is_file()

    scopes = set()
    for grammar in grammars:
        assert (VSCODE / grammar["path"]).is_file(), grammar["path"]
        scopes.add(grammar["scopeName"])
    assert "text.epresso" in scopes
    assert "text.epresso.injection" in scopes

    props = pkg["contributes"]["configuration"]["properties"]
    for setting in ("epresso.format.executablePath", "epresso.lsp.enable", "epresso.lsp.executablePath"):
        assert setting in props
    assert pkg["contributes"]["configurationDefaults"]["[epresso]"]["editor.defaultFormatter"] == "nikoshell.epresso"
    # extension.js requires the hand-rolled LSP client next to it
    assert (VSCODE / "lsp.js").is_file()


def test_manifest_declares_mit_and_ships_a_license():
    pkg = json.loads((VSCODE / "package.json").read_text(encoding="utf-8"))
    assert pkg["license"] == "MIT"
    assert (VSCODE / "LICENSE").is_file()


def test_grammars_parse_and_includes_resolve():
    for path in GRAMMARS:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["scopeName"]
        assert data["patterns"], f"{path.name}: no top-level patterns"
        repository = set(data.get("repository", {}))
        for include in _includes(data):
            if include.startswith("#"):
                assert include[1:] in repository, f"{path.name}: unknown rule {include}"
            elif "#" in include:
                continue  # scope#rule into another grammar
            else:
                assert include in EXTERNAL, f"{path.name}: unexpected include {include}"


def test_main_grammar_covers_frontmatter_and_ep_files():
    data = json.loads(GRAMMARS[0].read_text(encoding="utf-8"))
    assert "ep" in data["fileTypes"]
    assert "frontmatter" in data["repository"]
    assert "jinja" in data["repository"]
    assert "componentTag" in data["repository"]


def test_injection_grammar_is_scoped_to_epresso():
    data = json.loads(GRAMMARS[1].read_text(encoding="utf-8"))
    selector = data["injectionSelector"]
    assert "text.epresso" in selector
    assert "meta.frontmatter.epresso" in selector  # don't inject into Python frontmatter


def test_language_configuration_is_valid():
    data = json.loads((VSCODE / "language-configuration.json").read_text(encoding="utf-8"))
    assert data["comments"]["lineComment"] == "#"
    assert data["comments"]["blockComment"] == ["{#", "#}"]
    assert data["indentationRules"]["increaseIndentPattern"]
    assert data["indentationRules"]["decreaseIndentPattern"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("name", ["extension.js", "lsp.js"])
def test_javascript_files_parse(name: str):
    result = subprocess.run(
        ["node", "--check", str(VSCODE / name)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
