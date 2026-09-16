"""Layer resolution — directory, package and repo (tarball / clone) sources."""

from __future__ import annotations

import io
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

from epresso import layers
from epresso.config import load_config
from epresso.errors import ConfigError
from epresso.incremental import BuildGraph


def _write_site(root: Path, *sources: str):
    items = ", ".join(f'"{s}"' for s in sources)
    (root / "site.toml").write_text(f"[layers]\nuse = [{items}]\n", encoding="utf-8")
    return load_config(root)


def _layer_dir(root: Path, name: str = "vendor") -> Path:
    d = root / name
    (d / "components").mkdir(parents=True)
    (d / "components" / "Card.ep").write_text("---\n---\n<b>card</b>\n", encoding="utf-8")
    return d


# -- parsing ---------------------------------------------------------------


def test_parse_layer_forms():
    assert layers.parse_layer("./vendor/x").kind == "path"
    assert layers.parse_layer("path:/abs/x").value == "/abs/x"
    assert layers.parse_layer("pkg:epresso_ui").value == "epresso_ui"

    gh = layers.parse_layer("github:owner/repo@v1")
    assert gh.kind == "repo"
    assert gh.value == "https://github.com/owner/repo"
    assert gh.ref == "v1"

    g = layers.parse_layer("git+https://host/org/repo@main")
    assert g.kind == "repo" and g.ref == "main"
    # scp-style git URL: the userinfo "@" is not a ref
    assert layers.parse_layer("git@host:org/repo").ref is None


def test_parse_layer_rejects_empty():
    with pytest.raises(ConfigError, match="empty layer source"):
        layers.parse_layer("  ")


# -- directory / package sources ------------------------------------------


def test_path_layer_resolves(tmp_path):
    d = _layer_dir(tmp_path)
    assert [layer.root for layer in layers.resolve_layers(_write_site(tmp_path, "./vendor"))] == [d.resolve()]


def test_missing_path_layer_raises(tmp_path):
    with pytest.raises(ConfigError, match="layer directory not found"):
        layers.resolve_layers(_write_site(tmp_path, "path:./nope"))


def test_pkg_layer_resolves(tmp_path, monkeypatch):
    pkg = tmp_path / "site-packages" / "epresso_demo_components"
    (pkg / "components").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "components" / "Card.ep").write_text("---\n---\n<b>x</b>\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path / "site-packages"))
    assert layers.resolve_layers(_write_site(tmp_path, "pkg:epresso_demo_components"))[0].root == pkg.resolve()


def test_pkg_layer_without_component_dirs_raises(tmp_path, monkeypatch):
    pkg = tmp_path / "sp" / "epresso_demo_empty"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path / "sp"))
    with pytest.raises(ConfigError, match="no components/"):
        layers.resolve_layers(_write_site(tmp_path, "pkg:epresso_demo_empty"))


def test_duplicate_sources_are_deduped(tmp_path):
    _layer_dir(tmp_path)
    cfg = _write_site(tmp_path, "./vendor", "path:./vendor")
    assert len(layers.resolve_layers(cfg)) == 1


# -- repo sources ----------------------------------------------------------


def _tarball(top: str = "repo-v1") -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        data = b"---\n---\n<b>layer card</b>\n"
        info = tarfile.TarInfo(f"{top}/components/Card.ep")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class _Resp:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data

    def __enter__(self) -> _Resp:
        return self

    def __exit__(self, *_: object) -> bool:
        return False


def _pin_urlopen(monkeypatch, payload: bytes, seen: list[str]) -> None:
    def fake(url, timeout=None):  # noqa: ANN001, ANN202
        seen.append(url)
        return _Resp(payload)

    monkeypatch.setattr("urllib.request.urlopen", fake)


def test_github_layer_fetches_tarball_then_reuses_cache(tmp_path, monkeypatch):
    seen: list[str] = []
    _pin_urlopen(monkeypatch, _tarball(), seen)
    cfg = _write_site(tmp_path, "github:owner/repo@v1")

    root = layers.resolve_layers(cfg)[0].root
    assert (root / "components" / "Card.ep").is_file()
    assert (root / layers._MARKER).is_file()
    assert seen == ["https://github.com/owner/repo/archive/v1.tar.gz"]

    layers.resolve_layers(cfg)  # cache hit
    assert len(seen) == 1


def test_github_layer_without_ref_uses_HEAD(tmp_path, monkeypatch):
    seen: list[str] = []
    _pin_urlopen(monkeypatch, _tarball("repo-HEAD"), seen)
    layers.resolve_layers(_write_site(tmp_path, "github:owner/repo"))
    assert seen == ["https://github.com/owner/repo/archive/HEAD.tar.gz"]


def test_github_layer_download_failure_is_a_config_error(tmp_path, monkeypatch):
    def boom(url, timeout=None):  # noqa: ANN001, ANN202
        raise OSError("no network")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    with pytest.raises(ConfigError, match="could not download layer"):
        layers.resolve_layers(_write_site(tmp_path, "github:owner/repo@v1"))


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_generic_git_layer_shallow_clones_and_strips_history(tmp_path):
    repo = tmp_path / "repo"
    (repo / "components").mkdir(parents=True)
    (repo / "components" / "Card.ep").write_text("---\n---\n<b>git card</b>\n", encoding="utf-8")
    _git(repo, ["init", "-q"])
    _git(repo, ["add", "-A"])
    _git(repo, ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"])

    root = layers.resolve_layers(_write_site(tmp_path, f"git+file://{repo}"))[0].root
    assert (root / "components" / "Card.ep").is_file()
    assert not (root / ".git").exists()


def _git(cwd: Path, args: list[str]) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


# -- incremental hashing ---------------------------------------------------


def test_layer_files_feed_the_code_hash(tmp_path):
    layer = _layer_dir(tmp_path)
    cfg = load_config(tmp_path)
    before = BuildGraph.hash_code(cfg, [layer])
    without = BuildGraph.hash_code(cfg, [])
    (layer / "components" / "Card.ep").write_text("---\n---\n<b>changed</b>\n", encoding="utf-8")
    assert BuildGraph.hash_code(cfg, [layer]) != before
    assert BuildGraph.hash_code(cfg, []) == without  # ignored when not passed
