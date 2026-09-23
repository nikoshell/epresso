---
order: 342
---

# Plugins

Plugins extend epresso through a **capability registry**. A plugin is a named,
configurable object exposing lifecycle hooks; each hook receives a narrow
`Capabilities` handle — **never the raw `Site`** — so a plugin can only touch the
extension surface epresso exposes. Plugins are deterministic: deduplicated by
name, run in `priority` order, and re-loading a site never double-applies a
contribution. Bundled, runnable example plugins ship under `examples/plugins/`
(see [Bundled example plugins](#bundled-example-plugins)).

## Writing a plugin

Build a plugin with a **factory** so you can pass options:

```python
from epresso.plugins import Plugin

def greeter(*, text: str = "hello", shout: bool = False):
    def on_setup(caps):
        caps.add_global("greeting", lambda: text.upper() if shout else text)
        caps.add_filter("shout", lambda s: str(s).upper())
    return Plugin(name="greeter", hooks={"on_setup": on_setup})
```

A **subclass** style is also supported — `on_*` methods are collected
automatically:

```python
from epresso.plugins import Plugin

class Greeter(Plugin):
    name = "greeter"
    def on_setup(self, caps):
        caps.add_global("greeting", lambda: "hello")
```

## Capabilities

| Capability                | Valid in      | Effect                                              |
|---------------------------|---------------|-----------------------------------------------------|
| `add_global(name, value)` | `on_setup`    | expose a Jinja template global                      |
| `add_filter(name, fn)`    | `on_setup`    | register a Jinja template filter                    |
| `register_collection(...)`| `before_load` | add a content collection (via a loader) to the store |
| `add_markdown_extension(spec)` | `before_load` | register a Markdown extension (idempotent)      |
| `transform_html(fn)`      | any           | rewrite every rendered HTML page: `fn(html, ctx) -> html` |
| `inject_head(fragment)`   | any           | insert a fragment into `<head>` of every page      |

Each hook also receives `caps.config`, `caps.site`, and `caps.logger` (a
namespaced `[plugin:<name>]` logger; debug lines gate on
`EPRESSO_DEBUG=plugin:<name>`).

Using a capability at the wrong time raises a `CapabilityError` with a hint —
for example, `register_collection` must run in `before_load` so the collection
is loaded before content, and `add_global`/`add_filter` need the Jinja
environment, which exists from `on_setup` onward.

## Layers vs plugins

For **components and layouts** that live in another package or repo, prefer
[layers](layers.md) — a declarative `[layers] use` entry with no code to write.
Reach for a plugin when you need build-time behaviour: template globals, HTML
transforms, content collections, markdown extensions. A package can do both.

## Registering a collection from a plugin

`register_collection` plugs a loader into the same store as `content.config.py`:

```python
def quotes(items):
    def before_load(caps):
        caps.register_collection(
            "quotes",
            loader=lambda: [{"id": "a", "data": {"text": "stay deterministic"}}],
        )
    return Plugin(name="quotes", hooks={"before_load": before_load})
```

Templates then read it with `get_collection("quotes")` / `get_entry("quotes", …)`,
exactly like a `content.config.py` collection.

## Transforming rendered output

`transform_html(fn)` runs a pure function over each rendered HTML route. `ctx`
carries `{"path", "params"}` for the route:

```python
def watermark(text="Made by epresso"):
    def on_setup(caps):
        def transform(html, ctx):
            if "</pre>" not in html or "epresso-mark" in html:
                return html
            return html.replace("</pre>", f'<span class="epresso-mark">{text}</span></pre>')
        caps.transform_html(transform)
    return Plugin(name="watermark", hooks={"on_setup": on_setup})
```

Transforms are applied at render time in both build and dev. Because a transform
can depend on plugin code (not just content), a build that has any registered
transform re-renders every route rather than reusing a cached output — content
*body* caching still holds.

## Enabling

For **published** plugins, `uv add` the package and list it under `[plugins]` in
`site.toml` (dotted path — installable modules only):

```toml
plugins = ["epresso-greeter:greeter", "myorg:thing"]
```

For **local** plugins (or any that take options), add a `plugins.py` at the site
root that builds each plugin with its options and leaves `Plugin` instances as
module attributes:

```python
from greeter import greeter
greeting = greeter(text="hello from a plugin")
```

Options can only be passed via the code path (a dotted-path string cannot carry
them).

## Lifecycle & ordering

- Plugins are **deduplicated by name** — registering the same `name` twice raises
  a `PluginError`.
- Plugins run in **`priority` order** (lower first; ties keep registration order).
- Re-running a load/build is **idempotent** — contributions (globals, filters,
  collections, Markdown extensions, html transforms) are re-applied against a
  freshly built environment each load.

The lifecycle hooks, in order: `before_load`, `on_setup`, `after_load`,
`before_build`, `after_build(caps, result)`, `on_assets`.

## Bundled example plugins

Ready-made, runnable example plugins ship in `examples/plugins/`. Each module is
a real plugin you can read and copy into your own project:

| Module         | Demonstrates                                                                  | Capabilities used         |
|----------------|--------------------------------------------------------------------------------|---------------------------|
| `greeter.py`   | factory style + options + template hooks                                      | `add_global`, `add_filter` |
| `quotes.py`    | a content collection contributed at load time                                 | `register_collection` (`before_load`) |
| `watermark.py` | a pure html transform stamping a “Made by epresso” pill on every code block   | `transform_html`          |

A runnable demo site in `examples/plugins/demo/` wires all three and builds a
small page. From the repo root:

```bash
uv run epresso build examples/plugins/demo   # then open dist/index.html
```

`demo/plugins.py` shows the recommended **local** enablement pattern:
`sys.path`-insert the folder, build each plugin with its options via a factory,
and leave the resulting `Plugin` instances as module attributes for epresso to
discover. For **published** plugins, `uv add` the package and reference it from
`site.toml` (see [Enabling](#enabling)). The demo output shows a shouted
greeting, a shouted filter value, two quotes from a plugin-registered collection,
and a “Made by epresso” pill stamped inside every code block.
