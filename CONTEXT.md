# epresso

epresso is a Python-first static site generator: `.ep` routes and components, typed
content collections, scoped CSS, and deterministic incremental builds. This is the
project's ubiquitous language — the words the code, docs and ADRs use for the same
concepts. Where two words exist, the one below is the one to use.

## Language

### Sources & composition

**`.ep file`**:
An epresso source file: a Python frontmatter plus a Jinja body, in the role of a component or a layout.
_Avoid_: template, widget, partial, block

**Component**:
A server-rendered `.ep file` invoked as a tag (`<Card/>`, `{% component "Card" %}`), resolved from `components/` and then `layouts/`.
_Avoid_: template, widget, partial

**Layout**:
A component used as a page shell: it emits the document (or a region) and exposes `<slot/>`. It is a component, not a separate format.
_Avoid_: template, wrapper, shell

**Slot**:
A named placeholder in a component's body (`<slot name="x"/>`), filled by the caller's children.
_Avoid_: placeholder, outlet

**Default slot**:
The caller-supplied body of a component, bound in its template as `content`.
_Avoid_: children; "content" as a bare noun

**Props**:
A component's validated inputs, declared as a Pydantic `Props` model in its frontmatter and exposed to the body as `props`.
_Avoid_: attributes, parameters, data

**Frontmatter**:
The fenced block at the top of a source file — Python for `.ep`, YAML for Markdown.
_Avoid_: header, metadata

**Fragment**:
`<Fragment>…</Fragment>` or `<>…</>` — a grouping marker that renders no element, used to satisfy the one-root-per-branch rule.
_Avoid_: wrapper, group

### Routing

**Page**:
A source file under `pages/` — a Markdown page (`.md`), an `.ep` route, or an endpoint (`.py`).
_Avoid_: view, document

**Route**:
One resolved URL from a page, with its params and data. One page can fan out to many routes.
_Avoid_: path, URL

**Route pattern**:
A `pages/` file before expansion — its static, `{param}` and `[...spread]` segments and the kind of route it produces.
_Avoid_: template route

**Fan-out**:
Producing many routes from one `.ep` page, via `get_static_paths()`.
_Avoid_: expansion, generation

**Endpoint**:
A route that returns its content type and body directly instead of rendering a template — a `.py` page is always one, and an `.ep` page with `get()` is one.
_Avoid_: API route, handler

### Content

**Collection**:
A named group of entries, defined in `content.config.py` against an optional Pydantic schema.
_Avoid_: section, folder, table

**Entry**:
One record in a collection: its id, authored data, body, digest and rendered output. A page template sees the entry's authored data as `props` and `data`.
_Avoid_: item, document, record, post

**Loader**:
What turns files or external data into entries — `GlobLoader`, `PythonLoader`, or a `LoaderObject`.
_Avoid_: provider, adapter, source, driver

**Content digest**:
The hash of an entry's body and data (`content_digest`) that decides whether an incremental build must re-render it.
_Avoid_: checksum, hash, version

**Rendered content**:
A body rendered to HTML together with its heading and image metadata (`RenderedContent`, `entry.rendered`).
_Avoid_: content, output, HTML

**Computed data**:
Values a loader derives for an entry — order, grouping, a navigation model — kept out of the schema-validated `data` (`entry.computed`).
_Avoid_: metadata, extras

### Styling & client behaviour

**Scoped CSS**:
A component's `<style>` block, rewritten to carry `data-epresso-<hash>` on each selector so it matches only elements that component authored.
_Avoid_: local CSS, CSS modules, component CSS

**Author scoping**:
The rule that an element is scoped to the component that wrote it, never re-stamped by the component that renders it — so passed-in children keep the caller's scope.
_Avoid_: consumer scoping, CSS isolation

**Client script**:
A `<script>` block in an `.ep file`, extracted, bundled and injected once on every page using the component. Page-level, never per-element.
_Avoid_: island, hydration, client directive

### Extending

**Theme**:
A complete epresso project used as a starting point — `epresso new` copies or clones it into a new site.
_Avoid_: template, boilerplate, preset

**Layer**:
An external root of components and layouts imported at build time (`[layers] use`) from a path, package or repo; the site's own files always shadow it.
_Avoid_: extension, package; a layer is not a theme — it contributes no pages, styles or content

**Plugin**:
A named object exposing lifecycle hooks, discovered from `site.toml` or `plugins.py`, and handed a `Capabilities` handle rather than the `Site`.
_Avoid_: extension, addon, middleware

### Build & caching

**Build graph**:
The content-dependency edges recorded while a route renders (`BuildGraph`); it decides what an incremental build may reuse.
_Avoid_: dependency tree, DAG

**Incremental cache**:
The persisted index of rendered routes and the content digests each depends on (`IncrementalCache`, `.cache/incremental.json`); a route is reused only while its cache key and every digest still match.
_Avoid_: build cache, memo cache

**Rendered-body cache**:
Persisted Markdown-to-HTML bodies, keyed by entry digest (`RenderedBodyCache`, `.cache/rendered.json`); a body is reused only while the config-and-code hash still matches.
_Avoid_: content cache, body cache

**Render session**:
The per-build accumulator of side-band output — scoped CSS and client scripts (`RenderSession`) — written as one combined bundle per site.
_Avoid_: render context, page context

**Build output**:
Everything a build writes under `dist/` — the rendered routes plus every generated file (`dir_output()`).
_Avoid_: export, public, publish

**Generated file**:
A file epresso writes itself at the end of a build — sitemap, `robots.txt`, `llms.txt`, RSS, `404.html`, search index — and skips when the user provides their own.
_Avoid_: artifact, extra

**Markdown backend**:
The renderer chosen by `[markdown] backend` — `native` (markdown-it-py) or the optional `rust` accelerator, which must be installed.
_Avoid_: markdown engine, markdown parser
