"""CSS processing tests — PostCSS/Tailwind detection, processing, and fallback."""

from epresso.css import CSSProcessor


def _make(files, root=None):
    import tempfile
    from pathlib import Path

    d = str(root) if root else tempfile.mkdtemp()
    root = Path(d)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


def test_no_processor_inactive(tmp_path):
    root = _make({}, root=tmp_path)
    from epresso.config import load_config

    proc = CSSProcessor(load_config(root))
    assert proc.active is False


def test_detects_postcss_when_binary_present(tmp_path, monkeypatch):
    root = _make({"postcss.config.js": "module.exports = {};"}, root=tmp_path)
    monkeypatch.setattr("epresso.css.shutil.which", lambda name: "/bin/" + name if name == "postcss" else None)
    from epresso.config import load_config

    proc = CSSProcessor(load_config(root))
    assert proc.active is True
    kind, _cfg = proc._detected
    assert kind == "postcss"


def test_detects_tailwind_when_binary_present(tmp_path, monkeypatch):
    root = _make({"tailwind.config.js": "export default {};"}, root=tmp_path)
    monkeypatch.setattr("epresso.css.shutil.which", lambda name: "/bin/" + name if name == "tailwindcss" else None)
    from epresso.config import load_config

    proc = CSSProcessor(load_config(root))
    assert proc.active is True
    assert proc._detected[0] == "tailwind"


def test_process_falls_back_without_detection(tmp_path):
    root = _make({}, root=tmp_path)
    (root / "assets" / "css").mkdir(parents=True)
    entry = root / "assets" / "css" / "main.css"
    entry.write_text("a{}")
    from epresso.config import load_config

    proc = CSSProcessor(load_config(root))
    out = proc.process(entry, root / "dist")
    assert out is None  # no processor configured


def test_process_runs_tailwind_cli(tmp_path, monkeypatch):
    root = _make(
        {
            "tailwind.config.js": "export default {};",
            "assets/css/main.css": "@tailwind base;",
        },
        root=tmp_path,
    )
    from epresso.config import load_config

    monkeypatch.setattr("epresso.css.shutil.which", lambda name: "/bin/tailwindcss" if name == "tailwindcss" else None)
    proc = CSSProcessor(load_config(root))  # detect happens in __init__

    def fake_run(args, **kwargs):
        out = root / "dist" / "assets" / "css" / "main.css"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("/* processed */ base{}")

    monkeypatch.setattr("epresso.css.subprocess.run", fake_run)
    entry = root / "assets" / "css" / "main.css"
    out = proc.process(entry, root / "dist")
    assert out is not None
    assert out.read_text() == "/* processed */ base{}"


def test_detects_project_local_tailwind_cli(tmp_path):
    root = _make({}, root=tmp_path)
    (root / "node_modules" / ".bin").mkdir(parents=True)
    (root / "node_modules" / ".bin" / "tailwindcss").write_text("#!/usr/bin/env node\n")
    from epresso.config import load_config
    proc = CSSProcessor(load_config(root))
    assert proc.active is True
    assert proc._detected[0] == "tailwind"


def test_no_false_detect_without_project_tailwind(tmp_path):
    # a global tailwindcss on PATH must NOT trigger detection without a config
    # or a project-local CLI
    root = _make({}, root=tmp_path)
    from epresso.config import load_config
    proc = CSSProcessor(load_config(root))
    # simulate a global binary present but no project-local one / config
    proc._bin = lambda name: "/usr/bin/tailwindcss" if name == "tailwindcss" else None
    assert proc._detect() is None
