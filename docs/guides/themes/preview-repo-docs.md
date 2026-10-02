---
order: 364
---

# Preview a repository's docs

`epresso docs` renders a directory of Markdown as a documentation site and — when
that directory is a git checkout — **links every page back to its repository**. No
`site.toml` required.

## Render a repo's docs

Point it at a local clone, or give it the repository directly:

```bash
epresso docs ../my-repo                  # a local checkout
epresso docs github:owner/repo@v1        # clone + render (branch, tag, or commit-ish)
epresso docs https://github.com/owner/repo
```

A git source is shallow-cloned into `.cache/repos/` and reused on later runs
(`epresso clean` clears it). Because the clone keeps its `.git`, the pages link
back to the repository — see below.

epresso copies the bundled docs theme into a temporary project, injects the
Markdown as its docs collection, and serves the result on
`http://127.0.0.1:4321`. The sidebar tree, search index, and on-page table of
contents are all built from the Markdown itself.

For a git checkout, epresso copies the markdown under the docs directory (default
`docs/`, overridable with `EPRESSO_DOCS_DIR` or `REPO_DOCS`) plus a top-level
README, and skips build junk. A bare Markdown directory is copied whole.

## The link back to the repository

When the source is a git checkout, epresso reads its `origin` remote and default
branch and writes them into the generated project's `site.toml`:

```toml
[site]
repository = "https://github.com/you/my-repo"
branch = "main"
```

Those two fields drive the **view / edit this source** links on every page, so the
preview points at the real repository rather than the theme's own. The source path
is recorded as `docs_source`, and the collection it populates as
`[theme] docs_base` — see [Configuration](/guides/build/configuration/) for those
fields.

If the directory you pass already has its own `site.toml`, epresso builds it as-is
and its own `[site] repository` / `branch` decide the links.

## Use your own theme

`--theme` replaces the bundled docs theme:

```bash
epresso docs ../my-repo --theme ../my-theme
```

The theme project is copied and re-pointed at your Markdown, so any docs theme
works — see [Create a theme](/guides/themes/create-a-theme/).

## Write a static build

`--out` skips the server and writes a production build — useful for CI:

```bash
epresso docs ../my-repo --out dist/docs
```

The output is an ordinary static site; deploy `dist/docs/` anywhere. For a project
that already has its own `site.toml`, `epresso build` is the direct route.

## Branding

The docs theme ships no brand of its own: the header shows your project's name
(the repository or directory name, or `title` in `docs.toml`) and the site uses
the default favicon. Brand it by putting files next to your docs:

| File | Becomes |
|------|---------|
| `logo.svg` | the header logo (shown instead of the name) |
| `favicon.ico` | the favicon |
| `og-image.png` | the social preview image (`og:image`) |
| `styles.css` / `style.css` | appended to the theme stylesheet, so its variable overrides win |

Or set them explicitly in `[theme]` (`logo`, `favicon`, `og_image`, as paths
under the output root); an explicit key wins over a file.

## Next

- [CLI reference](/reference/cli/) — every flag for `docs`, `serve`, and the rest.
- [Start from a template](/guides/themes/from-template/) — `epresso new` for a
  project you keep.
