---
title: Code-heavy page
description: Almost entirely fenced code, to isolate Pygments and the code-component path.
---

# Code-heavy page

A page whose cost is dominated by syntax highlighting: a dozen fenced blocks in
several languages, some with a filename info string, one routed to a code
component.

```python
from pathlib import Path


def walk(root: Path, suffix: str = ".md") -> list[Path]:
    """Every matching file under root, sorted for determinism."""
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix == suffix)


def render_all(root: Path, render) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in walk(root):
        out[str(path)] = render(path.read_text(encoding="utf-8"))
    return out
```

```python
class Store:
    def __init__(self) -> None:
        self._by_name: dict[str, list[object]] = {}

    def register(self, name: str, value: object) -> None:
        self._by_name.setdefault(name, []).append(value)

    def get(self, name: str) -> list[object]:
        return self._by_name.get(name, [])
```

```typescript
type Route = { path: string; data: unknown };

export function match(routes: Route[], path: string): Route | undefined {
  return routes.find((r) => r.path === path);
}
```

```javascript
const cache = new Map();

export function memo(key, compute) {
  if (!cache.has(key)) cache.set(key, compute());
  return cache.get(key);
}
```

```bash
#!/usr/bin/env bash
set -euo pipefail

for file in bench/*.md; do
  printf '%s\n' "$(basename "$file")"
done
```

```tree
content/
  posts/
    hello.md
    second-post.md
  docs/
    guides/
      index.md
```

```json
{
  "name": "epresso",
  "version": "0.4.0",
  "private": false,
  "dependencies": ["markdown-it-py", "pygments"]
}
```

```yaml
site:
  name: Example
  url: https://example.com
build:
  trailing_slash: always
```

```rust
fn render(input: &str) -> String {
    input.lines().map(|l| format!("<p>{l}</p>")).collect()
}
```

```sql
SELECT collection, COUNT(*) AS n
FROM entries
WHERE draft = false
GROUP BY collection
ORDER BY n DESC;
```

```html
<section class="card">
  <h2>Title</h2>
  <p>Body copy.</p>
</section>
```

```diff
- old line
+ new line
```
