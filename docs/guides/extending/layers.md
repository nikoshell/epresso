# Layers

Layers let a site use components and layouts that live in **another repo or
directory** — without copying them in. Declare them in `site.toml`:

```toml
[layers]
use = [
  "./vendor/components",                 # a directory
  "pkg:epresso_ui",                      # an installed Python package
  "github:owner/epresso-components@v1",  # a repo, pinned to a tag
]
```

Then use them exactly like your own components:

```epresso
<Button variant="primary">Save</Button>
```

## What a layer is

A layer is a directory shaped like a site root. epresso reads two of its
subdirectories:

```tree
my-components/
  components/        # <Name>.ep, resolved by basename across subdirs
  layouts/           # shell components (searched after components/)
```

Everything else in the directory is ignored. Per-component scoped `<style>` and
`<script>` work exactly as they do for site components, so a layer carries its
own styles and behaviour with no extra setup. Global CSS travels in a
`<style is:global>` block inside a component.

## Sources

| Form | Example | How it is fetched |
|------|---------|-------------------|
| directory | `./vendor/components`, `path:/abs/dir` | used in place |
| package | `pkg:epresso_ui` | `importlib` — must be installed (`uv add <pkg>`) |
| GitHub repo | `github:owner/repo@v1`, `https://github.com/owner/repo@v1` | release tarball (no `git` needed) |
| other git | `git+https://host/org/repo@v1`, `git@host:org/repo` | shallow `git clone --depth=1` |

Remote sources are downloaded once into `.cache/layers/` and reused. The `@ref`
(tag, branch, or commit) is part of the cache path, so changing it fetches a
different revision; delete `.cache/layers/` to re-fetch a moved tag. Without a
ref, the repository's `HEAD` is used — pin a ref for reproducible builds.

## Override order

The site always wins:

```tree
site/ components/  layouts/     ← searched first
─────────────────────────────
layer 1  (first entry in [layers].use)
layer 2
...
```

A site file with the same basename overrides the layer's; among layers, the
first declared wins. Use `<Name:subdir />` to disambiguate explicitly when two
roots ship the same basename. Run `epresso layers` to see what resolved where:

```console
$ epresso layers
Layers (the site's own components/ + layouts/ win; then these in order):
  path  ./vendor/components
        → /home/me/site/vendor/components
  repo  github:owner/epresso-components@v1
        → /home/me/site/.cache/layers/github.com__owner__epresso-components@v1-1a2b3c4d
```

## Editing a layer

* A **directory** layer is live: edit it and rebuild — `epresso dev` watches
  layer directories outside the project too.
* A **repo** layer is a cached snapshot: push a new tag upstream and bump the
  `@ref`, or clear `.cache/layers/`.

## Scope

v1 layers contribute `components/` and `layouts/` only. They do **not**
contribute `pages/`, `content/`, `styles/`, `assets/` or `site.toml` — the site
owns those. Global CSS belongs in a component's `<style is:global>`; an
external component that needs an image should use inline SVG or a site-owned
asset.

## Packages vs plugins

`pkg:` is only a convenient way to point at an installed package's directory. A
package that needs to do work at build time (register globals, transform HTML,
add a collection) should ship a [Plugin](plugins.md) instead — the two are
independent and can be combined.

## UnoCSS / Tailwind caveat

If a layer's components are styled with utility classes that are scanned out of
the component files at build time (e.g. UnoCSS `@source`), a consumer's scan
config will not see files living in another repo or in `.cache/layers/`. Ship
**prebuilt** CSS in the layer rather than depending on the consumer's utility
build.
