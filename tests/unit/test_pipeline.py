"""Unit tests for the shared pipeline helpers (file_digest, bundle_js)."""

from epresso.pipeline import bundle_js, file_digest


def test_file_digest_is_deterministic_and_sensitive(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("hello", encoding="utf-8")
    b.write_text("hello", encoding="utf-8")
    a2 = tmp_path / "a2.txt"
    a2.write_text("hellx", encoding="utf-8")
    assert file_digest(a) == file_digest(b)
    assert file_digest(a) != file_digest(a2)


def test_file_digest_length_truncation(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"\x00" * 1024)
    full = file_digest(p)
    assert len(full) == 64
    assert file_digest(p, 12) == full[:12]
    assert file_digest(p, 10) == full[:10]


def test_file_digest_is_large_file_safe(tmp_path):
    p = tmp_path / "big.bin"
    p.write_bytes(b"x" * (1 << 20))  # 1 MiB — streamed, not read at once
    assert file_digest(p) == file_digest(p)


def test_bundle_js_missing_when_esbuild_absent(tmp_path, monkeypatch):
    # Point PATH at an empty dir so esbuild cannot be found -> "missing".
    empty = tmp_path / "bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    result, detail = bundle_js(["a.js"])
    assert result == "missing"
    assert detail == ""
