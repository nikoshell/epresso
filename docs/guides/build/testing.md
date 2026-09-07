# Testing

epresso sites are static, which makes them easy to test. Use **pytest** and assert
on the build output.

## Unit-test frontmatter / helpers

`.ep` page/component frontmatter is Python — import and unit-test it directly
(crumbs builders, loaders, content helpers).

## Build + assert on output

Build the site, then assert on generated files:

```python
import subprocess, pathlib

def test_build_output(tmp_path):
    subprocess.run(["epresso", "build", str(tmp_path)], check=True)
    out = tmp_path / "dist"
    assert (out / "index.html").exists()
    assert "Hello" in (out / "index.html").read_text()
```

## End-to-end

Serve the built `dist/` (or `epresso dev`) and drive it with your browser/e2e tool
of choice (`httpx` for headers, Playwright if you need JS). Because pages are
plain HTML, a simple HTTP GET covers most behavior.

epresso itself is tested with `pytest` (unit) + integration tests against the dev
server. Run them with `uv run pytest`.
